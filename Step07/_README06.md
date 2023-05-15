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
