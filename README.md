# CQ4DS-babyagi-refactoring-exercise

poetry init -n
poetry config virtualenvs.in-project true
poetry env use python3.10
poetry add black
poetry install
poetry add python-dotenv typer openai pinecone-client lancedb

[tool.black]
skip-string-normalization = true
line-length = 120
