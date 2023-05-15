import os
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

load_dotenv('../.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.getenv('PINECONE_ENVIRONMENT')

YOUR_TABLE_NAME = 'test-table'
OBJECTIVE = 'Solve world hunger.'
YOUR_FIRST_TASK = 'Develop a task list.'

openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

table_name = YOUR_TABLE_NAME
dimension = 1536
metric = 'cosine'
pod_type = 'p1'
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

index = pinecone.Index(table_name)

task_list = deque([])


def add_task(task):
    task_list.append(task)


def get_ada_embedding(text):
    text = text.replace('\n', ' ')
    return openai.Embedding.create(input=[text], model='text-embedding-ada-002')['data'][0]['embedding']


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
