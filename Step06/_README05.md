### Step 05: Move all the rest of the code into the BabyAGI class

- Turn global functions into member functions (add `self` to the function signature and move them under the BabyAGI class)
- Turn any reference to global variables and constants into access of properties (add `self.` before the variable name)
- Replace reference to global constants to properties (e.g. OBJECTIVE -> self.objective as this is now part of BabyAGI class

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
