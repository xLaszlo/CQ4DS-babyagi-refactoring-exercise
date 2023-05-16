### Step 09: Task class

- Write the task class (see example). This will integrate every component of the task class and will be built on the go. All the interfaces that used parts of it before will get this class (prompt (originally called "name"), response, vector, id).

- Change the `task_list` property to use tasks, check every occurence where it is updated (`add_task`)
- Construct a class and pass that instead of a part
- Rewrite the interface (both "real" and test double's) to use Task classes (check out the examples for ideas)

Note: This exercise removes multiple type of code smells
- "Primitive Obsession": Using primitive types instead of objects, code is hard to extend later
- "Data Clumps": Different datatypes always appear together
- "Long Parameter List": Because each part of the class needs to passed on parameter lists are extended


```
class Task:
    def __init__(self, name, id=None, result=None, vector=None):
        self.name = name
        self.id = id
        self.result = result
        self.vector = vector
```

Note: The class can be constructed purely from a prompt ("name" with original terminology) and default everything else to None, this might not be ideal but I avoid dealing with this to maintain brevity.
