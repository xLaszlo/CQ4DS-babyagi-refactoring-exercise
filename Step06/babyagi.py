import os
import typer
from dotenv import load_dotenv
import openai
import pinecone
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
        text = text.replace('\n', ' ')
        return openai.Embedding.create(input=[text], model='text-embedding-ada-002')['data'][0]['embedding']


class PineconeService:
    def __init__(self, api_key, environment, table_name, dimension, metric, pod_type):
        self.table_name = table_name
        pinecone.init(api_key=api_key, environment=environment)
        if table_name not in pinecone.list_indexes():
            pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)
        self.index = pinecone.Index(table_name)


class BabyAGI:
    def __init__(self, objective, ai_service, vector_service):
        self.objective = objective
        self.ai_service = ai_service
        self.vector_service = vector_service
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
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=0.5,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        new_tasks = response.choices[0].text.strip().split('\n')
        return [
            {'task_name': task_name}
            for task_name in new_tasks  # <-- dictionary instead of class, 'primitive obsession'?
        ]

    def prioritization_agent(self, this_task_id):
        task_names = [t['task_name'] for t in self.task_list]
        next_task_id = int(this_task_id) + 1
        prompt = PRIORITIZATION_PROMPT.format(
            task_names=task_names, objective=self.objective, next_task_id=next_task_id
        )
        response = openai.Completion.create(
            engine='text-davinci-003',  #                 <-- this API call is similar to the previous function's
            prompt=prompt,  #                             <-- maybe extract a common function with defaults
            temperature=0.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        new_tasks = response.choices[0].text.strip().split('\n')
        self.task_list = deque()
        for task_string in new_tasks:  #                  <-- loop with a lot of stuff, maybe comprehensions?
            task_parts = task_string.strip().split('.', 1)
            if len(task_parts) == 2:
                task_id = task_parts[0].strip()
                task_name = task_parts[1].strip()
                self.task_list.append({'task_id': task_id, 'task_name': task_name})  # <-- dictionary again

    def execution_agent(self, task) -> str:
        context = self.context_agent(query=self.objective, n=5)
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=EXECUTION_PROMPT.format(objective=self.objective, task=task),
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].text.strip()

    def context_agent(self, query, n):
        query_embedding = self.ai_service.get_ada_embedding(query)
        results = self.vector_service.index.query(query_embedding, top_k=n, include_metadata=True)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata['task'])) for item in sorted_results]

    def run(self, first_task):
        print(self.objective)
        first_task = {'task_id': 1, 'task_name': first_task}
        self.add_task(first_task)
        task_id_counter = 1
        for _ in range(4):
            if self.task_list:
                task = self.task_list.popleft()
                print(task['task_name'])
                result = self.execution_agent(task['task_name'])
                print(result)
                this_task_id = int(task['task_id'])
                enriched_result = {'data': result}
                result_id = f'result_{task["task_id"]}'
                vector = enriched_result['data']
                self.vector_service.index.upsert(
                    [
                        (
                            result_id,
                            self.ai_service.get_ada_embedding(vector),
                            {'task': task['task_name'], 'result': result},
                        )
                    ]
                )
            new_tasks = self.task_creation_agent(enriched_result, task['task_name'])

            for new_task in new_tasks:
                task_id_counter += 1
                new_task.update({'task_id': task_id_counter})
                self.add_task(new_task)
            self.prioritization_agent(this_task_id)


def main():
    load_dotenv()
    baby_agi = BabyAGI(
        objective='Solve world hunger.',
        ai_service=OpenAIService(api_key=os.getenv('OPENAI_API_KEY')),
        vector_service=PineconeService(
            api_key=os.getenv('PINECONE_API_KEY'),
            environment=os.getenv('PINECONE_ENVIRONMENT'),
            table_name='test-table',
            dimension=1536,
            metric='cosine',
            pod_type='p1',
        ),
    )
    baby_agi.run(first_task='Develop a task list.')


if __name__ == '__main__':
    typer.run(main)
