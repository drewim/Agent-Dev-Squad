from agent import Agent
import time
from typing import Dict, Any
from api.ollama_client import OllamaClient


class TestDevAgent(Agent):
    """
    Agent responsible for creating unit tests.
    """
    DEFAULT_SYSTEM_PROMPT = "You are a highly experienced software developer with expertise in developing unit and system tests for python code.\
        Provide a confidence score from 0-1 that the code will accomplish its purpose."
    
    def __init__(self, name, model, message_pipeline, task_queue, logger=None, confidence_threshold=0.7, system_prompt = None):
        super().__init__(name, model, message_pipeline, task_queue, logger=logger, confidence_threshold=confidence_threshold)
        self.ollama_client = OllamaClient(logger=self.logger)
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = self.DEFAULT_SYSTEM_PROMPT

    def run(self):
        """
        Main loop for the Test Dev.
        """
        self.logger.info(f"{self.name} is running...")
        while True:
            # Check for unreviewed tasks
            self.logger.debug("Checking for tasks...")
            untested_tasks = [task for task in self.task_queue.values() if task['assigned_agent'] == self.id and task['status'] == 'pending']
            if untested_tasks:
                # Get the first task
                task = untested_tasks[0]
                self.start_task(task['task_id'])
                self.process_task(task)
            time.sleep(1)

    def process_task(self, task_details: Dict[str, Any]):
        """
        Example implementation to provide tests.
        """
        if not task_details:
            self.logger.error("No task details provided.")
            return

        if 'output' not in task_details:
            self.logger.error("Task output is missing")
            self.fail_task("No output given.")
            return
        if 'description' not in task_details:
             self.logger.error("Task description not provided")
             self.fail_task("No description given")
             return

        code = task_details['output']
        description = task_details['description']
        self.logger.info(f"Generating test for {description[:30]}...")  # Log the task id being worked on, with a shorter version of the description
         # Placeholder: Replace with actual test generation logic (LLM call here)
        prompt = f"{self.system_prompt} Create python unit test using pytest for '{description}'. Make sure the tests can be run with pytest, and return the tests within triple backticks: {code}"
        model_name = task_details.get('resource_requirements', {}).get('model', self.model) # Get model name from task, or use default
        test_code = self.ollama_client.generate_text(model_name, prompt) # make ollama API call

        if not test_code:
            self.logger.error("Could not get a response from the ollama API")
            self.fail_task("Could not generate tests")
            return
        confidence = 0.8 # Set confidence for this agent, in a real situation this would come from the model

        if confidence >= self.confidence_threshold:
            self.complete_task({'tests': test_code}) # if confident, then pass on the tests
        else:
            self.request_help("Confidence is low, I think these tests need help")
            self.pause_task("Waiting for help with tests")


    def get_status(self):
        """
        Returns the status of the test dev.
        """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'current_task_id': self.current_task_id,
            'is_active': self.is_active,
            'ollama_client': self.ollama_client.get_status()
        }