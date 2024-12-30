from src.agents.agent import Agent
import time
# import uuid
from typing import Dict, Any
from src.api.ollama_client import OllamaClient
from src.api.response_schema import ArchitectResponse

class ArchitectAgent(Agent):
    """
    Agent responsible for breaking down project into smaller tasks.
    """
    def __init__(self, name, model, message_pipeline, task_queue, logger=None, confidence_threshold=0.7):
        super().__init__(name, model, message_pipeline, task_queue, logger=logger, confidence_threshold=confidence_threshold)
        self.ollama_client = OllamaClient(logger=self.logger)

    def run(self):
        """
        Main loop for the Architect. Currently just a placeholder.
        """
        self.logger.info(f"{self.name} is running...")
        while True:
            # Check for any unassigned tasks, break up the largest one
            # This could also be set to fire on user input to start the process, or on a timer
            self.logger.debug("Checking tasks...")
            unassigned_tasks = [task for task in self.task_queue.values() if task['assigned_agent'] is None]
            if unassigned_tasks:
                # Get the largest task, and break it up
                self.logger.debug("found an unassigned task...")
                # Sort by the length of the description, so largest tasks are at the end
                largest_task = sorted(unassigned_tasks, key=lambda task: len(task['description']))[-1]
                self.process_task(largest_task) # pass the largest task to the processing function
            time.sleep(1) # Wait 1 second, not to overwhelm the system

    def process_task(self, task_details: Dict[str, Any]):
        """
        Example implementation to break up a large task using an LLM
        """
        if not task_details:
            self.logger.error("No task details provided for processing.")
            return

        if 'description' not in task_details:
             self.logger.error("Task description not provided")
             return

        description = task_details['description']

        self.logger.info(f"Breaking down task: {description}")
         # Placeholder: Replace with actual task breakdown logic (LLM call here)
        prompt = f"Break down the following task: '{description}' into small coding subtasks that can be completed by small AI coding models. Provide each subtask description on its own line and output a structured response."
        model_name = task_details.get('resource_requirements', {}).get('model', self.model) # Get model name from task, or use default
        response = self.ollama_client.generate_text(model_name, prompt, system_prompt=self.DEFAULT_SYSTEM_PROMPT, response_model=ArchitectResponse) # make ollama API call
        if not response:
            self.logger.error("Could not get response from Ollama")
            self.fail_task("Could not get response for task")
            return

        if not isinstance(response, ArchitectResponse):
             self.logger.error(f"Could not parse response {response}")
             self.fail_task(f"Could not parse response {response}")
             return

        if response.confidence < self.confidence_threshold:
            self.logger.warning(f"Low confidence for task: {description} ({response.confidence}), requesting help.")
            self.request_help(f"Low confidence from LLM {response.confidence}")
            self.pause_task(f"Waiting for help for low confidence response {response.confidence}")
            return
        subtask_descriptions = response.response.split('\n') # Split into different subtasks
        if len(subtask_descriptions) < 2:
            self.logger.error(f"Could not parse enough subtasks: {subtask_descriptions}")
            self.fail_task(f"Could not parse enough subtasks: {subtask_descriptions}")
            return

        subtask_1_id = self.create_task(
             description=subtask_descriptions[0],
             dependencies=[task_details['task_id']],
            priority= task_details.get('priority', 1),
             resource_requirements={
                 'model': self.model
            },
            # system_prompt = f"You are a subtask assistant and your job is to perform a subtask" # add system prompt for subtasks
        )
        subtask_2_id = self.create_task(
            description=subtask_descriptions[1],
            dependencies=[task_details['task_id']],
            priority= task_details.get('priority', 1),
             resource_requirements={
                 'model': self.model
            },
            # system_prompt = f"You are a subtask assistant and your job is to perform a subtask" # add system prompt for subtasks
        )


        # Set the old task as complete
        self.complete_task({
            'message': 'Task has been broken down and subtasks have been created',
             'subtasks': [subtask_1_id, subtask_2_id]
        })

    def get_status(self):
        """
        Returns the status of the architect.
        """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'current_task_id': self.current_task_id,
            'is_active': self.is_active,
            'ollama_client': self.ollama_client.get_status()
        }
 