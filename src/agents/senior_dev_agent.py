from agent import Agent
import time
from typing import Dict, Any
from api.ollama_client import OllamaClient


class SeniorDevAgent(Agent):
    """
    Agent responsible for reviewing code and providing feedback.
    """
    DEFAULT_SYSTEM_PROMPT = "You are an expert software developer specialized in the review and optimization of code. After assessing \
        and/or improving the code if needed, provide a confidence score from 0-1 that the code will accomplish its purpose."
    
    def __init__(self, name, model, message_pipeline, task_queue, logger=None, confidence_threshold = 0.8, system_prompt = None):
        super().__init__(name, model, message_pipeline, task_queue, logger=logger, confidence_threshold=confidence_threshold)
        self.ollama_client = OllamaClient(logger=self.logger)
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = self.DEFAULT_SYSTEM_PROMPT

    def run(self):
        """
        Main loop for the Senior Dev.
        """
        self.logger.info(f"{self.name} is running...")
        while True:
            # Check for unreviewed tasks
            self.logger.debug("Checking for tasks...")
            unreviewed_tasks = [task for task in self.task_queue.values() if task['assigned_agent'] == self.id and task['status'] == 'pending']
            if unreviewed_tasks:
                # Get the first task
                task = unreviewed_tasks[0]
                self.start_task(task['task_id'])
                self.process_task(task)
            time.sleep(1)

    def process_task(self, task_details: Dict[str, Any]):
        """
        Example implementation to provide feedback.
        """

        if not task_details:
            self.logger.error("No task details provided.")
            return

        if 'output' not in task_details:
            self.logger.error("Task output is missing.")
            self.fail_task("No output provided.")
            return

        if 'description' not in task_details:
             self.logger.error("Task description not provided")
             self.fail_task("No description provided.")
             return


        code = task_details['output']
        description = task_details['description']
        self.logger.info(f"Reviewing code for task {task_details['task_id']}: {description[:30]}...") # Log the task id being worked on, with a shorter version of the description
        # Placeholder: Replace with actual code review logic (LLM call here)
        model_name = task_details.get('resource_requirements', {}).get('model', self.model) # Get model name from task, or use default
        prompt = f"{self.system_prompt} Review the following code for '{description}'.  Respond with what to improve, optimize or if the code is good: {code}"
        feedback = self.ollama_client.generate_text(model_name, prompt) # make ollama API call
        if not feedback:
            self.logger.error("Could not get a response from the ollama API")
            self.fail_task("Could not get a response for code review")
            return
        # If good enough confidence
        confidence = 0.9 # Set confidence for this agent
        if confidence >= self.confidence_threshold:
             # create a test task
             self.logger.info("Confidence is high, creating test task")
             test_task_id = self.create_task(
                 description = f"Create unit tests for '{description[:30]}'",
                 dependencies = [task_details['task_id']],
                 priority = task_details.get('priority', 1),
                 resource_requirements={
                     'model': 'llama-2-13b'
                 },
                output = code # send along the code so the test dev agent can read this
             )
             self.complete_task({'feedback': feedback, 'test_task_id': test_task_id})
        else:
             self.request_help("Confidence is low, I think this needs more help")
             self.pause_task("Waiting for help with code review.")


    def get_status(self):
        """
        Returns the status of the Senior Dev.
        """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'current_task_id': self.current_task_id,
            'is_active': self.is_active,
            'ollama_client': self.ollama_client.get_status()
        }