from agent import Agent
import time
from typing import Dict, Any
from api.ollama_client import OllamaClient

class JuniorDevAgent(Agent):
    """
    Agent responsible for code generation.
    """
    DEFAULT_SYSTEM_PROMPT = "You are a python software developer responsible for successfully completing small coding subtasks.\
        Complete your task to the best of your ability and provide a confidence level from 0-1 that your response will accomplish the task."
    def __init__(self, name, model, message_pipeline, task_queue, logger=None, confidence_threshold=0.6, system_prompt=None):
        super().__init__(name, model, message_pipeline, task_queue, logger=logger, confidence_threshold=confidence_threshold)
        self.ollama_client = OllamaClient(logger=self.logger) # create a new instance of ollama client
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = self.DEFAULT_SYSTEM_PROMPT

    def run(self):
        """
        Main loop for the Junior Dev.
        """
        self.logger.info(f"{self.name} is running...")
        while True:
            # Check for unassigned tasks
            self.logger.debug("Checking for tasks...")
            unassigned_tasks = [task for task in self.task_queue.values() if task['assigned_agent'] == self.id and task['status'] == 'pending']
            if unassigned_tasks:
                # Get the first unassigned task
                task = unassigned_tasks[0]
                self.start_task(task['task_id'])
                self.process_task(task) # pass the task to the processor
            time.sleep(1)

    def process_task(self, task_details: Dict[str, Any]):
        """
        Example implementation for code generation using Ollama.
        """
        if not task_details:
            self.logger.error("No task details provided.")
            return

        if 'description' not in task_details:
             self.logger.error("Task description not provided.")
             self.fail_task("No task description given.")
             return

        description = task_details['description']
        self.logger.info(f"Generating code for: {description[:30]}...") # log a short version of the description
        # Placeholder: Replace with actual code generation logic (LLM call here)
        prompt = f"Generate python code to '{description}'. Respond with code only and make sure it is surrounded in triple backticks." # a simple prompt for now
        model_name = task_details.get('resource_requirements', {}).get('model', self.model) # Get model name from task, or use default
        code = self.ollama_client.generate_text(model_name, prompt) # make ollama API call

        if not code:
             self.logger.error("Could not get a response from the ollama API")
             self.fail_task("Could not generate code")
             return
        
        confidence = 0.7 # Set confidence for this agent, in a real situation this would come from the model (can be determined by parsing the response as well)
        if confidence >= self.confidence_threshold:
            self.complete_task({'code': code}) # if confident, then pass on the code
        else:
             self.request_help("Confidence is low, I think this code needs help")
             self.pause_task("Waiting for help generating code")



    def get_status(self):
        """
        Returns the status of the Junior Dev.
        """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'current_task_id': self.current_task_id,
            'is_active': self.is_active,
            'ollama_client': self.ollama_client.get_status() # return the status of the ollama client as well
        }