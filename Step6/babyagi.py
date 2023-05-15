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


    def task_creation_agent(objective, result, task_description, task_list):
        prompt = TASK_CREATION_PROMPT.format(
            objective=objective,
            result=result,
            task_description=task_description,
            task_list=', '.join([t['task_name'] for t in task_list]),
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
        return [{'task_name': task_name} for task_name in new_tasks]


    def prioritization_agent(this_task_id):
        global task_list
        task_names = [t['task_name'] for t in task_list]
        next_task_id = int(this_task_id) + 1
        prompt = PRIORITIZATION_PROMPT.format(task_names=task_names, objective=OBJECTIVE, next_task_id=next_task_id)
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=0.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        new_tasks = response.choices[0].text.strip().split('\n')
        task_list = deque()
        for task_string in new_tasks:
            task_parts = task_string.strip().split('.', 1)
            if len(task_parts) == 2:
                task_id = task_parts[0].strip()
                task_name = task_parts[1].strip()
                task_list.append({'task_id': task_id, 'task_name': task_name})


    def execution_agent(objective, task):
        context = context_agent(index=YOUR_TABLE_NAME, query=objective, n=5)
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=EXECUTION_PROMPT.format(objective=objective, task=task),
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        return response.choices[0].text.strip()


    def context_agent(query, index, n):
        query_embedding = get_ada_embedding(query)
        index = pinecone.Index(index_name=index)
        results = index.query(query_embedding, top_k=n, include_metadata=True)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata['task'])) for item in sorted_results]


    first_task = {'task_id': 1, 'task_name': YOUR_FIRST_TASK}

    add_task(first_task)
    task_id_counter = 1
    for _ in range(4):
        if task_list:
            task = task_list.popleft()
            result = execution_agent(OBJECTIVE, task['task_name'])
            this_task_id = int(task['task_id'])
            enriched_result = {'data': result}
            result_id = f'result_{task["task_id"]}'
            vector = enriched_result['data']
            index.upsert([(result_id, get_ada_embedding(vector), {'task': task['task_name'], 'result': result})])

        new_tasks = task_creation_agent(OBJECTIVE, enriched_result, task['task_name'], [t['task_name'] for t in task_list])

        for new_task in new_tasks:
            task_id_counter += 1
            new_task.update({'task_id': task_id_counter})
            add_task(new_task)
        prioritization_agent(this_task_id)


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
