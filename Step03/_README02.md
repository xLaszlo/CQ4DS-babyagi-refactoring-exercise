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
