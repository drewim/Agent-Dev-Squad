import psutil
import torch
import logging
from typing import Dict, Any
from src.utils.config import get_config_value

class ResourceManager:
    """
    Manages system resources and agent availability.
    """

    def __init__(self, config: Dict[str, Any], logger=None):
         self.config = config
         if logger:
              self.logger = logger
         else:
              self.logger = logging.getLogger("resource_manager")
              self.logger.setLevel(logging.DEBUG)
              ch = logging.StreamHandler()
              formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
              ch.setFormatter(formatter)
              self.logger.addHandler(ch)
         self.agent_resources = {} # Track resource usage of agents by agent_id
         self.api_limit = get_config_value(self.config, 'api_limit', 10)
         self.api_count = 0 # track how many api calls have been made
         self.max_memory = self._get_total_memory()
         self.max_vram = self._get_total_vram()
         self.logger.info(f'Total Memory: {self.max_memory:.2f} GB')
         if self.max_vram:
              self.logger.info(f'Total VRAM: {self.max_vram:.2f} GB')
         self.model_resource_map = {
             'llama-2-7b': {'memory': 2.0, 'vram': 2.0},
             'llama-2-13b': {'memory': 8.0, 'vram': 8.0},
             'gpt-4': {'memory': 16.0, 'vram': 16.0},
             # Add more model resource requirements here
             'default': {'memory': 2.0, 'vram': 2.0} # If model is not in the list then use the default
         }

    def _get_total_memory(self) -> float:
        """
        Get the total system memory.
        """
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)

    def _get_total_vram(self) -> float | None:
        """
        Get the total GPU memory (VRAM), will return none if there is no vram to monitor
        """
        if torch.backends.mps.is_available():
             try:
                # TODO: Update cuda call to mps
                mps_device = torch.device("mps")
                total_vram = torch.cuda.get_device_properties(0).total_memory
                return total_vram / (1024 ** 3)
             except Exception as e:
                  self.logger.warning(f'Error getting VRAM: {e}')
                  return None
        else:
            self.logger.info("CUDA is not available on this system, skipping VRAM monitoring.")
            return None
    def track_agent_resource(self, agent_id, resource_usage: Dict[str, Any]):
        """
        Track the resource usage of a specific agent.
        """
        self.agent_resources[agent_id] = resource_usage
        self.logger.debug(f"Tracked resources for agent {agent_id}: {resource_usage}")

    def get_available_resources(self) -> Dict[str, Any]:
        """
        Get available system resources.
        """
        cpu_percent = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory()
        memory_percent = memory_usage.percent
        available_memory = (memory_usage.available / (1024 ** 3))
        vram_percent = 0
        available_vram = 0
        if torch.cuda.is_available():
             try:
                vram = torch.cuda.memory_summary()
                vram_percent = vram['reserved_max'] / vram['total'] * 100
                available_vram = (vram['total']-vram['reserved_max'])/(1024**3)
             except Exception as e:
                  self.logger.warning(f'Error getting available vram: {e}')

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'available_memory': available_memory,
            'vram_percent': vram_percent,
            'available_vram': available_vram,
            'agents': self.agent_resources # Add the agent resources
        }


    def get_agent_resource_usage(self, agent_id: str) -> Dict[str, Any]:
        """
        Get the resource usage for a particular agent.
        """
        if agent_id in self.agent_resources:
            return self.agent_resources[agent_id]
        return {}


    def can_run_task(self, task_details: Dict[str, Any]) -> bool:
        """
        Check if there are enough resources to run a task.
        """
        resource_requirements = task_details.get("resource_requirements", {}) # Default empty dict
        if not resource_requirements:
            self.logger.info(f"Task {task_details.get('task_id', 'Unknown')} has no resource requirements")
            return True # no resource requirements

        model = resource_requirements.get('model', 'default')  # Default small model
        required_resources = self.get_model_resources(model)
        available_resources = self.get_available_resources()

        if available_resources['available_memory'] < required_resources['memory']:
            self.logger.warning(f"Not enough memory for task {task_details.get('task_id', 'Unknown')}: Required {required_resources['memory']:.2f} GB, available {available_resources['available_memory']:.2f} GB")
            return False
        
        if torch.cuda.is_available() and available_resources['available_vram'] < required_resources['vram']: # Check vram if available
            self.logger.warning(f"Not enough VRAM for task {task_details.get('task_id', 'Unknown')}: Required {required_resources['vram']:.2f} GB, available {available_resources['available_vram']:.2f} GB")
            return False

        self.logger.info(f"Resources available for task {task_details.get('task_id', 'Unknown')}")
        return True

    def get_model_resources(self, model_size: str) -> Dict[str, float]:
         """
         Gets the memory used by a given model size, returns default if it does not exist
         """
         return self.model_resource_map.get(model_size, self.model_resource_map.get('default'))

    def check_api_usage(self) -> bool:
         """
         Checks if there are more api calls available, returns true if there are
         """
         return self.api_count < self.api_limit

    def increment_api_usage(self):
         """
         Increments the number of api calls
         """
         self.api_count += 1

    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the resource manager.
        """
        return {
            'api_calls_made': self.api_count,
            'max_api_calls': self.api_limit,
            'total_memory': self.max_memory,
            'total_vram': self.max_vram,
            'available_resources': self.get_available_resources(),
            'model_resource_map': self.model_resource_map # return the current models, and resource usage
        }