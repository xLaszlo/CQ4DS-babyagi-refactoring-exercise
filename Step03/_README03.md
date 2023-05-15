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
