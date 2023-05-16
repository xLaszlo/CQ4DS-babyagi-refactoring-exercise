### Step 00: Original for reference

- Read and review code
### Step 01: Cleanse code

- Remove comments
- Remove type hints (for now)
- Remove print statements
- Move api keys to .env file in the main repository directory (see example below)
- Get api keys from environment with load_dotenv() and os.getenv()

```
FILENAME: .env LOCATION: CQ4DS-babyagi-refactoring-exercise/
---- START ----
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=asia-northeast1-gcp
---- END ----
```

Note: this file is in .gitignore so you won't store it in github and make it public accidentally
### Step 02: Clean Architecture

- Move code into classes (OpenAIService, PineconeService, BabyAGI)
- Set up production context with `main()` function
- Inline as many constants as possible (apart from PROMPTS)
- Use typer for simply CLI implementation
- Start with openai api calls

This step drafts the Clean Architecture. BabyAGI will be the business logic, OpenAIService and PineconeService the Adapter Design Patterns for external services. BabyAGI's `run()` function will implement the "Inversion of Control". The `main()` function sets up the slow "production" context, which we will later swap to the fast "test" context where we replace the adapters to "test doubles", classes that look like the real ones but internal just fake the API calls.

The structure should look like this:

```
class OpenAIService:
    ...
class PineconeService:
    ...
class BabyAGI:
    ...
    def run(...):
       while True:
            ...
def main():
    baby_agi = BabyAGI(
        ai_service=OpenAIService(...),
        vector_service=PineconeService(...),
        ...
    )
    baby_agi.run(...)

if __name__ == '__main__':
    typer.run(main)
```
### Step 03: Pinecone service class

- Continue with pinecone api calls

Note: This is just the first step of moving code broken down into several steps. The code is not executable yet.

The structure should look like this:

```
class OpenAIService:
    ...
class PineconeService:
    ...
class BabyAGI:
    ...
    def run(...):
       while True:
            ...
def main():
    baby_agi = BabyAGI(
        ai_service=OpenAIService(...),
        vector_service=PineconeService(...),
        ...
    )
    baby_agi.run(...)

if __name__ == '__main__':
    typer.run(main)
```
### Step 04: Create BabyAGI class

- Continue with BabyAGI class
- Inline the constants

Note: This is just the first step of moving code broken down into several steps. The code is not executable yet.

The structure should look like this:

```
class OpenAIService:
    ...
class PineconeService:
    ...
class BabyAGI:
    ...
    def run(...):
       while True:
            ...
def main():
    baby_agi = BabyAGI(
        ai_service=OpenAIService(...),
        vector_service=PineconeService(...),
        ...
    )
    baby_agi.run(...)

if __name__ == '__main__':
    typer.run(main)
```
### Step 05: Move all the rest of the code into the BabyAGI class

- Turn global functions into member functions (add `self` to the function signature and move them under the BabyAGI class)
- Turn any reference to global variables and constants into access of properties (add `self.` before the variable name)
- Replace reference to global constants to properties (e.g. OBJECTIVE -> self.objective as this is now part of BabyAGI class

Note: At this point the code should run. If anything is not working fix it based on the error messages. run it with `python babyagi.py`

The structure should look like this:

```
class OpenAIService:
    ...
class PineconeService:
    ...
class BabyAGI:
    ...
    def run(...):
       while True:
            ...
def main():
    baby_agi = BabyAGI(
        ai_service=OpenAIService(...),
        vector_service=PineconeService(...),
        ...
    )
    baby_agi.run(...)

if __name__ == '__main__':
    typer.run(main)
```
### Step 06: Better adapter classes

BabyAGI's functions are still accessing the external services directly. To decouple from them and enable further refactoring by replacing them with test doubles these need to be swapped to

- Find all code when a BabyAGI function accesses part of an external service (openai or pinecone) and does _not_ use an injected dependency's  (self.ai_service or self.vector_service) interface (member function): e.g.: in `context_agent`, `self.vector_service.index.query`.

These are dependencies on the actual implementation of the service the Adapter is hiding. So in the case of `self.vector_service.index.query`, if this to be replaced by a test double that new one must have a `.index` member variable as well. This is clearly a detail that shouldn't be exposed. The BabyAGI class should only know that it has a `vector_service` adapter injected and it has a `query()` interface it can call to get results.

- Write a function in `PineconeService`
- Move the relevant code that calls `self.vector_service.index.query` into it
- Write the signature so the previous call gets all the relevant variables
- Rewrite the place where `self.vector_service.index.query` to use `PineconeService`'s new function

Repeath the same exercise with `openai.Completion.create()`. Technically this is a global service call because of the way opeani implemented it but the idea is the same. Because this function has so many parameters the ones that are fixed with all calls are defaulted with the common value. This can be refactored later if it causes inconvenience.

The next steps will write the testdoubles and swap the real adapters with the new ones. If any calls to the injected services are not refactored this will fail acting as an extra check.
### Step 07: Test doubles

- Write the `TestAIService` class that has the same interface (same member functions with the same signature / arguments) as `OpenAIService`. Inject the real `OpenAIService` as a depedency. Maintain an internal cache which stores the prompt, response pairs and returns the relevant ones. If the prompt is not in the cache call the real service and add it to the cache.
- Write a `LanceService` class that has the same interface as `PineconeService`. Use LanceDB (similar to SQLite but for vector databases)
- Add these two terms to `.gitignore` so they don't pollute the repository: `babyagi_cache.pkl`, `test-table.lance/`

Note: It is OK to copy-paste and then review the code from the examples. Both techniques are frequently used so do review both.

Note2: Running the code the second time should be near instant as there are no external calls, prompt responses come from the cache and LanceDB is very fast (and)

Note3: Caveat: LLMs are not deterministic and even if temperature is set to 0 they can create different outputs which lead to cache misses and that require `TestAIService` to call `OpenAIService` and that is slow. Should be relatively rare.
### Step 08: Inline and preparation for Task class

- Inline as variables so there are less code to refactor when we bring in the Task class
- Inline `context_agent` and `execution_agent` so the calls don't need to traced through several jumps. They can be reintroduced later
- Look out for improper scoping (a variable declared far from where it is used e.g.: `task_id_counter`)

Note: The code should run between too changes and each run should be very fast due to the cache.
### Step 09: Task class

- Write the task class (see example). This will integrate every component of the task class and will be built on the go. All the interfaces that used parts of it before will get this class (prompt (originally called "name"), response, vector, id).

- Change the `task_list` property to use tasks, check every occurence where it is updated (`add_task`)
- Construct a class and pass that instead of a part
- Rewrite the interface (both "real" and test double's) to use Task classes (check out the examples for ideas)

Note: This exercise removes multiple type of code smells
- "Primitive Obsession": Using primitive types instead of objects, code is hard to extend later
- "Data Clumps": Different datatypes always appear together
- "Long Parameter List": Because each part of the class needs to passed on parameter lists are extended


```
class Task:
    def __init__(self, name, id=None, result=None, vector=None):
        self.name = name
        self.id = id
        self.result = result
        self.vector = vector
```

Note: The class can be constructed purely from a prompt ("name" with original terminology) and default everything else to None, this might not be ideal but I avoid dealing with this to maintain brevity.
### Step 10: Task class - cleanup

- Replace the remaining dictionary based tasks with classes
- task_creation_agent() returns a list of strings that are converted into tasks and added to the queue. This should happen in task_creation_agent(). Move this code there
- task ID management happens in add_task() (if a task doesn't have an ID it adds one higher than the currently highest ones), Remove code related to this (e.g.: task_id_counter in task_creation_agent())
- In the main loop the core block only runs if there are tasks in the list. Turn this into a "Guard clause": Check if list is empty and stop the program with exit(0). Note: while `if lst:` is a valid condition for testing if a list's is empty making it explicit helps readability: `if len(lst) == 0:` is a better solution.
- Extract the top task execution into its own function (execution_agent)

This concludes the exercise.
