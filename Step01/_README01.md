### Step 01: Cleanse code

- Remove comments
- Remove type hints (for now)
- Remove print statements
- Move api keys to .env file in the main repository directory (see example below)
- Get api keys from environment with load_dotenv() and os.getenv()


FILENAME: .env LOCATION: CQ4DS-babyagi-refactoring-exercise/
---- START ----
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=asia-northeast1-gcp
---- END ----

Note: this file is in .gitignore so you won't store it in github and make it public accidentally
