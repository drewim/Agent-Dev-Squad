from agent import Agent
import time
from typing import Dict, Any
import logging


class ProjectManagerAgent(Agent):
    """
    Agent responsible for monitoring project status and providing updates.
    """
    DEFAULT_SYSTEM_PROMPT = ""
    def __init__(self, name, model, message_pipeline, task_queue, resource_manager, logger=None, confidence_threshold=0.9, system_prompt=None):
        super().__init__(name, model, message_pipeline, task_queue, logger=logger, confidence_threshold=confidence_threshold)
        self.resource_manager = resource_manager # Add the resource manager
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = self.DEFAULT_SYSTEM_PROMPT

    def run(self):
        """
        Main loop for the Project Manager.
        """
        self.logger.info(f"{self.name} is running...")
        while True:
            self.process_task() # Call the processing function
            time.sleep(5) # check status every 5 seconds

    def process_task(self, task_details: Dict[str, Any] = None):
        """
        Monitors the Task Queue and provides project updates.
        """
        if task_details:
            self.logger.warning("Project manager cannot process a task assigned to it, please check config")

        total_tasks = len(self.task_queue)
        pending_tasks = len([task for task in self.task_queue.values() if task['status'] == 'pending'])
        in_progress_tasks = len([task for task in self.task_queue.values() if task['status'] == 'in_progress'])
        completed_tasks = len([task for task in self.task_queue.values() if task['status'] == 'completed'])
        failed_tasks = len([task for task in self.task_queue.values() if task['status'] == 'failed'])
        paused_tasks = len([task for task in self.task_queue.values() if task['status'] == 'paused'])
        
        resources = self.resource_manager.get_status()

        status_report = f"""
        --- Project Status ---
        Total Tasks: {total_tasks}
        Pending Tasks: {pending_tasks}
        In Progress Tasks: {in_progress_tasks}
        Completed Tasks: {completed_tasks}
        Failed Tasks: {failed_tasks}
        Paused Tasks: {paused_tasks}
        API calls made: {resources['api_calls_made']}/{resources['max_api_calls']}
        Total Memory: {resources['total_memory']:.2f} GB
        Total VRAM: {resources['total_vram']:.2f} GB
        Available resources: {resources['available_resources']}
        """
        self.logger.info(status_report)

    def get_status(self):
        """
        Returns the status of the project manager.
        """
        return {
            'id': self.id,
            'name': self.name,
            'model': self.model,
            'current_task_id': self.current_task_id,
            'is_active': self.is_active
        }