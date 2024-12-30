**Workflow:**

1. **Project Initialization:**
    - The Architect creates initial tasks and adds them to the Task Queue based on input tasks from the user
2. **Task Scheduling:**
    - The Scheduler periodically checks the Task Queue for pending tasks and resource availability.    
    - Tasks are assigned to agents based on capabilities, priorities, and available resources.    
3. **Task Execution:**
    - Assigned agents start working on their tasks and report their status through the Message Pipeline        
    - Junior Devs generate code.
    - Test Dev Agent creates corresponding unit tests.
    - Senior Dev reviews Junior Dev's code and provides feedback, code changes, and updates code in the repo.
4. **Help Requests:**
    - If an agent is unsure of how to proceed, it can request help through the message pipeline to the senior dev or via the external API if needed (or to pause the task).    
5. **Completion and Updates:**
    - Agents update the Task Queue with task status (completed, failed, in_progress).    
    - The Project Manager monitors overall progress.    
6. **Iteration:**
    - Repeat steps 2-5 until the project is complete.
