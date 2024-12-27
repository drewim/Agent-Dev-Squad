import uuid
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any

class Agent(ABC):
    """
    Abstract base class for all agents.
    """

    def __init__(self, name: str, model: str, message_pipeline, task_queue, confidence_threshold: float = 0.6, logger=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.model = model  # Model name or identifier
        self.message_pipeline = message_pipeline  # Communication channel
        self.task_queue = task_queue
        self.confidence_threshold = confidence_threshold # Confidence required to move forward
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(f"agent_{self.name}_{self.id}")
            self.logger.setLevel(logging.DEBUG) # Default log level can be changed as needed
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        self.current_task_id = None
        self.is_active = False

    @abstractmethod
    def run(self):
        """
        Abstract method for the agent's main loop.
        """
        pass

    def start_task(self, task_id):
        """
        Called when the scheduler sends a task to the agent.
        """
        self.logger.info(f"Starting task: {task_id}")
        self.current_task_id = task_id
        self.is_active = True

    def complete_task(self, result: Dict[str, Any]):
        """
        Called after an agent has completed the current task
        """
        self.logger.info(f"Task {self.current_task_id} complete")
        self.is_active = False
        self.current_task_id = None
        self.update_task_status('completed', result)


    def fail_task(self, error_message: str):
        """
        Called if the agent cannot complete a task.
        """
        self.logger.error(f"Task {self.current_task_id} failed: {error_message}")
        self.is_active = False
        self.current_task_id = None
        self.update_task_status('failed', error_message)


    def pause_task(self, message: str = ""):
        """
        Called when the agent gets stuck and can't proceed without input.
        """
        self.logger.warning(f"Task {self.current_task_id} paused, {message}")
        self.is_active = False
        self.update_task_status('paused', message)


    def update_task_status(self, status: str, output: Any = None):
        """
        Updates the task status in the task queue.
        """
        task = self.task_queue.get(self.current_task_id)
        if task:
            task['status'] = status
            if output:
                task['output'] = output
            self.task_queue.set(self.current_task_id, task)
            self.message_pipeline.publish('task_update', {
                'task_id': self.current_task_id,
                'status': status,
                'agent_id': self.id
            })
        else:
             self.logger.error(f"Could not find task {self.current_task_id}")


    def request_help(self, message: str):
        """
        Requests assistance from another agent.
        """
        self.logger.info(f"Requesting help for task {self.current_task_id}: {message}")
        self.message_pipeline.publish("request_help", {
            "task_id": self.current_task_id,
            "agent_id": self.id,
            "message": message
        })

    def create_task(self, description: str, dependencies: list = None, priority: int = 1, resource_requirements: dict = None, output: any = None):
         """
         Creates a new task and adds it to the task queue
         """
         if not dependencies:
            dependencies = []
         if not resource_requirements:
              resource_requirements = {}
         task = {
            'task_id': str(uuid.uuid4()),
            'description': description,
            'dependencies': dependencies,
            'status': 'pending',
            'assigned_agent': None,
            'priority': priority,
            'resource_requirements': resource_requirements,
            'output': output
        }
         self.task_queue.set(task['task_id'], task)
         self.logger.info(f"Created new task: {task['task_id']}")
         return task['task_id']


    @abstractmethod
    def process_task(self, task_details):
        """
        Abstract method that gets called when a task is assigned and should process the actual work.
        """
        pass

    @abstractmethod
    def get_status(self):
        """
        Returns a dictionary of the agent's status. Useful for monitoring purposes.
        """
        pass