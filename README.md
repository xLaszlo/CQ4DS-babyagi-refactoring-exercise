# CQ4DS-babyagi-refactoring-exercise

The goal of this exercise is to move a simple LLM based program (BabyAGI) to the Clean Architecture. The short span (<200 lines), the simple data model (a single "task" class) and the presence of two external services (OpenAI and Pinecone) makes it a good educational material. See the original code in Step00

The rought steps are (See detailed instruction in the PR and in `INSTRUCTIONS.md`):

- Set up Clean Architecture
    - Main class for BabyAGI
    - Adapter class for external services
- Write test doubles (fast but fake classes that behave like the original one) for each service (cache for OpenAI and LanceDB for Pinecone)
- Swap the original adapters with the test doubles
- Replace task related variables with a single task class

Concepts in the exercise:
- Structural concepts:
    - Clean Architecure
    - Dependency Injection
    - Inversion of Control
    - Production and Test Contexts
- Programming concepts:
    - Adapter Design Pattern
    - Test Doubles
- Readability concepts:
    - Code smells
    - Primitive Obsession
    - Feature Envy
    - Long Parameter List
    - Inlining
    - Guard Clause
    - "Happy path on the left"

## Setup

If you start from scratch this is a set of commands to set up poetry and black:

```
poetry init -n
poetry config virtualenvs.in-project true
poetry env use python3.10
poetry add black
poetry install
poetry add python-dotenv typer openai pinecone-client lancedb
source .venv/bin/activate
```

To set the line length for black add this to `pyproject.toml`. `skip-string-normalization` stops `black` from turning single quotes into double quotes.

```
[tool.black]
skip-string-normalization = true
line-length = 120
```
