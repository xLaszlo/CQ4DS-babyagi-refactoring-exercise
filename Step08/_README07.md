### Step 07: Test doubles

- Write the `TestAIService` class that has the same interface (same member functions with the same signature / arguments) as `OpenAIService`. Inject the real `OpenAIService` as a depedency. Maintain an internal cache which stores the prompt, response pairs and returns the relevant ones. If the prompt is not in the cache call the real service and add it to the cache.
- Write a `LanceService` class that has the same interface as `PineconeService`. Use LanceDB (similar to SQLite but for vector databases)
- Add these two terms to `.gitignore` so they don't pollute the repository: `babyagi_cache.pkl`, `test-table.lance/`

Note: It is OK to copy-paste and then review the code from the examples. Both techniques are frequently used so do review both.
