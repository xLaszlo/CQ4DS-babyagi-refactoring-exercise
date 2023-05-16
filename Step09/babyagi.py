import os
import typer
import pickle
import pandas as pd
from dotenv import load_dotenv
import openai
import pinecone
import lancedb
import pyarrow as pa
from collections import deque


TASK_CREATION_PROMPT = """
You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective:
{objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}.
These are incomplete tasks: {task_list}. Based on the result, create new tasks to be completed by the AI system that
do not overlap with incomplete tasks. Return the tasks as an array."""

PRIORITIZATION_PROMPT = """
You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing
the following tasks: {task_names}. Consider the ultimate objective of your team:{objective}. Do not remove any tasks.
Return the result as a numbered list, like:
#. First task
#. Second task
Start the task list with number {next_task_id}."""

EXECUTION_PROMPT = """
You are an AI who performs one task based on the following objective: {objective}. Your task: {task}\nResponse:
"""


class OpenAIService:
    def __init__(self, api_key):
        openai.api_key = api_key

    def get_ada_embedding(self, text):
        return openai.Embedding.create(input=[text.replace('\n', ' ')], model='text-embedding-ada-002')['data'][0][
            'embedding'
        ]

    def create(self, prompt, max_tokens=100, temperature=0.5):
        return (
            openai.Completion.create(
                engine='text-davinci-003',
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            .choices[0]
            .text.strip()
        )


class TestAIService:
    def __init__(self, ai_service, cache_file):
        self.ai_service = ai_service
        self.cache_file = cache_file
        if os.path.isfile(cache_file):
            self.cache = pickle.load(open(cache_file, 'rb'))
        else:
            self.cache = {'ada': {}, 'create': {}}
            pickle.dump(self.cache, open(cache_file, 'wb'))

    def get_ada_embedding(self, text):
        if text not in self.cache['ada']:
            self.cache['ada'][text] = self.ai_service.get_ada_embedding(text)
            pickle.dump(self.cache, open(self.cache_file, 'wb'))
        return self.cache['ada'][text]

    def create(self, prompt, max_tokens=100, temperature=0.5):
        key = (prompt, max_tokens, temperature)
        if key not in self.cache['create']:
            self.cache['create'][key] = self.ai_service.create(prompt, max_tokens, temperature)
            pickle.dump(self.cache, open(self.cache_file, 'wb'))
        return self.cache['create'][key]


class PineconeService:
    def __init__(self, api_key, environment, table_name, dimension, metric, pod_type):
        self.table_name = table_name
        pinecone.init(api_key=api_key, environment=environment)
        if table_name not in pinecone.list_indexes():
            pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)
        self.index = pinecone.Index(table_name)

    def query(self, query_embedding, top_k):
        results = self.index.query(query_embedding, top_k=top_k, include_metadata=True)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata['task'])) for item in sorted_results]

    def upsert(self, data):
        self.index.upsert(data)


class LanceService:
    def __init__(self, table_name, dimension):
        self.db = lancedb.connect('.')
        schema = pa.schema(
            [
                pa.field('result_id', pa.string()),
                pa.field('vector', pa.list_(pa.float32(), dimension)),
                pa.field('task', pa.string()),
                pa.field('result', pa.string()),  # TODO There is a fixed schema but we keep converting
            ]
        )
        data = [{'result_id': 0, 'vector': [0.0] * dimension, 'task': 'asd', 'result': 'asd'}]
        self.table = self.db.create_table(table_name, mode='overwrite', data=data, schema=schema)

    def query(self, query_embedding, top_k):
        result = self.table.search(query_embedding).limit(top_k).to_df()
        return [v for v in result['task']]

    def upsert(self, data):
        data = {  # TODO This doesn't look good, why are we converting?
            'result_id': data[0][0],
            'vector': data[0][1],
            'task': data[0][2]['task'],
            'result': data[0][2]['result'],
        }
        self.table.add(pd.DataFrame([data]))


class BabyAGI:
    def __init__(self, objective, ai_service, vector_service):
        self.ai_service = ai_service
        self.vector_service = vector_service
        self.objective = objective
        self.objective_embedding = self.ai_service.get_ada_embedding(self.objective)
        self.task_list = deque([])

    def add_task(self, task):
        self.task_list.append(task)

    def task_creation_agent(self, result, task_description):
        prompt = TASK_CREATION_PROMPT.format(
            objective=self.objective,
            result=result,
            task_description=task_description,
            task_list=', '.join([t['task_name'] for t in self.task_list]),
        )
        return [{'task_name': task_name} for task_name in self.ai_service.create(prompt).split('\n')]

    def prioritization_agent(self, this_task_id):
        prompt = PRIORITIZATION_PROMPT.format(
            task_names=[t['task_name'] for t in self.task_list],
            objective=self.objective,
            next_task_id=int(this_task_id) + 1,
        )
        new_tasks = self.ai_service.create(prompt, max_tokens=1000).split('\n')
        self.task_list = deque()
        for task_string in new_tasks:
            task_parts = task_string.strip().split('.', 1)
            if len(task_parts) == 2:
                task_id = task_parts[0].strip()
                task_name = task_parts[1].strip()
                self.task_list.append({'task_id': task_id, 'task_name': task_name})

    def run(self, first_task):
        print(self.objective)
        self.add_task({'task_id': 1, 'task_name': first_task})
        for _ in range(4):
            if self.task_list:
                context = self.vector_service.query(self.objective_embedding, 5)

                task = self.task_list.popleft()
                print(task['task_name'])
                result = self.ai_service.create(
                    prompt=EXECUTION_PROMPT.format(objective=self.objective, task=task),
                    max_tokens=2000,
                    temperature=0.7,
                )
                print(result)
                this_task_id = int(task['task_id'])
                self.vector_service.upsert(
                    [
                        (
                            f'result_{task["task_id"]}',
                            self.ai_service.get_ada_embedding(result),
                            {'task': task['task_name'], 'result': result},
                        )
                    ]
                )
            new_tasks = self.task_creation_agent({'data': result}, task['task_name'])
            task_id_counter = 1
            for new_task in new_tasks:
                task_id_counter += 1
                new_task.update({'task_id': task_id_counter})
                self.add_task(new_task)
            self.prioritization_agent(this_task_id)


def main():
    load_dotenv()
    baby_agi = BabyAGI(
        objective='Solve world hunger.',
        ai_service=TestAIService(
            ai_service=OpenAIService(api_key=os.getenv('OPENAI_API_KEY')),
            cache_file='babyagi_cache.pkl',
        ),
        vector_service=LanceService(
            table_name='test-table',
            dimension=1536,
        )
        # vector_service=PineconeService(
        #     api_key=os.getenv('PINECONE_API_KEY'),
        #     environment=os.getenv('PINECONE_ENVIRONMENT'),
        #     table_name='test-table',
        #     dimension=1536,
        #     metric='cosine',
        #     pod_type='p1',
        # ),
    )
    baby_agi.run(first_task='Develop a task list.')


if __name__ == '__main__':
    typer.run(main)
