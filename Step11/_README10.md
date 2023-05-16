### Step 10: Task class - cleanup

- Replace the remaining dictionary based tasks with classes
- task_creation_agent() returns a list of strings that are converted into tasks and added to the queue. This should happen in task_creation_agent(). Move this code there
- task ID management happens in add_task() (if a task doesn't have an ID it adds one higher than the currently highest ones), Remove code related to this (e.g.: task_id_counter in task_creation_agent())
- In the main loop the core block only runs if there are tasks in the list. Turn this into a "Guard clause": Check if list is empty and stop the program with exit(0). Note: while `if lst:` is a valid condition for testing if a list's is empty making it explicit helps readability: `if len(lst) == 0:` is a better solution.
- Extract the top task execution into its own function (execution_agent)

This concludes the exercise.
