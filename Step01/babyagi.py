import typer
import openai  #                                      <-- major imports indicate external dependencies
import pinecone  #                                    <-- good opportunity to decouple
from collections import deque
from typing import Dict, List

OPENAI_API_KEY = ''  #                                <-- configs spread at the top
PINECONE_API_KEY = ''  #                              <-- should be tied with the place it is used
PINECONE_ENVIRONMENT = 'us-east1-gcp'

YOUR_TABLE_NAME = 'test-table'  #                     <-- these might better be command line parameters
OBJECTIVE = 'Solve world hunger.'
YOUR_FIRST_TASK = 'Develop a task list.'

openai.api_key = OPENAI_API_KEY  #                    <-- hardcoded initialisation
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
#                                                     ^-- better to make it local at construction

table_name = YOUR_TABLE_NAME
dimension = 1536
metric = 'cosine'
pod_type = 'p1'
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the index                                <-- trivial comment
index = pinecone.Index(table_name)

# Task list                                           <-- trivial comment
task_list = deque([])  #                              <-- reader will understand this from the code
#                                                     <-- also talks about "task_list" but not "task"


def add_task(task: Dict):  #                          <-- so far no sign of the "BabyAGI"
    task_list.append(task)  #                         <-- this part looks like a "proto" service


def get_ada_embedding(text):  #                       <-- calls to an external service (maybe decouple?)
    text = text.replace('\n', ' ')
    return openai.Embedding.create(input=[text], model='text-embedding-ada-002')['data'][0]['embedding']


#                                                     v-- long parameter list, "task" class might help
def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = ''.format(
        objective=objective, result=result, task_description=task_description, task_list={', '.join(task_list)}
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
        {'task_name': task_name} for task_name in new_tasks  # <-- dictionary instead of class, "primitive obsession"?
    ]


def prioritization_agent(this_task_id: int):
    global task_list  #                               <-- global variable? Could be part of main service
    task_names = [t['task_name'] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = ''.format(task_name=task_names, objective=OBJECTIVE, next_task_id=next_task_id)
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
    task_list = deque()  #                            <-- this overrides a global variable, investigate
    for task_string in new_tasks:  #                  <-- loop with a lot of stuff, maybe comprehensions?
        task_parts = task_string.strip().split('.', 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({'task_id': task_id, 'task_name': task_name})  # <-- dictionary again


def execution_agent(objective: str, task: str) -> str:
    context = context_agent(
        index=YOUR_TABLE_NAME, query=objective, n=5
    )  #                                              <-- this is unused (not printed either in original)
    response = openai.Completion.create(
        engine='text-davinci-003',
        prompt=''.format(objective=objective, task=task),
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].text.strip()


def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)  #       <-- first use of pinecone, should be a service call
    results = index.query(query_embedding, top_k=n, include_metadata=True)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata['task'])) for item in sorted_results]


# Add the first task                                  <-- trivial comment, reader will know this from var names
first_task = {'task_id': 1, 'task_name': YOUR_FIRST_TASK}

add_task(first_task)
# Main loop                                           <-- trivial comment
task_id_counter = 1
while True:  #                                         <-- this should be the core of the main function
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

# The main and external services should be initialised here
# with parameters and command line arguments
# There should be a "task" class that stores all the related elements:
# class Task:
#     ...
# class OpenAIService:
#     ...
# class PineconeService:
#     ...
# class BabyAGI:
#     ...
#     def run(...):
#        while True:
#             ...
# def main():
#     baby_agi = BabyAGI(
#         ai_service=OpenAIService(...),
#         vector_service=PineconeService(...),
#         ...
#     )
#     baby_agi.run(...)

# if __name__ == '__main__':
#     typer.run(main)
