### Step 08: Inline and preparation for Task class

- Inline as variables so there are less code to refactor when we bring in the Task class
- Inline `context_agent` and `execution_agent` so the calls don't need to traced through several jumps. They can be reintroduced later
- Look out for improper scoping (a variable declared far from where it is used e.g.: `task_id_counter`)

Note: The code should run between too changes and each run should be very fast due to the cache.
