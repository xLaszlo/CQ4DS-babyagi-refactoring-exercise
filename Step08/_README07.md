### Step 07: Test doubles

- Write the `TestAIService` class that has the same interface (same member functions with the same signature / arguments) as `OpenAIService`. Inject the real `OpenAIService` as a depedency. Maintain an internal cache which stores the prompt, response pairs and returns the relevant ones. If the prompt is not in the cache call the real service and add it to the cache.
- Write a `LanceService` class that has the same interface as `PineconeService`. Use LanceDB (similar to SQLite but for vector databases)
- Add these two terms to `.gitignore` so they don't pollute the repository: `babyagi_cache.pkl`, `test-table.lance/`

Note: It is OK to copy-paste and then review the code from the examples. Both techniques are frequently used so do review both.

Note2: Running the code the second time should be near instant as there are no external calls, prompt responses come from the cache and LanceDB is very fast (and)

Note3: Caveat: LLMs are not deterministic and even if temperature is set to 0 they can create different outputs which lead to cache misses and that require `TestAIService` to call `OpenAIService` and that is slow. Should be relatively rare.
