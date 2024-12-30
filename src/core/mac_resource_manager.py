import psutil
# import torch
import logging
from typing import Dict, Any
from src.utils.config import get_config_value

class MacResourceManager:
    """
    Manages system resources and agent availability for Apple Silicon MacBooks.
    """

    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger("mac_resource_manager")
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        
        self.agent_resources = {}  # Track resource usage of agents by agent_id
        self.api_limit = get_config_value(self.config, 'api_limit', 10)
        self.api_count = 0
        self.max_memory = self._get_total_memory()
        self.max_unified_memory = self._get_unified_memory()
        
        self.logger.info(f'Total System Memory: {self.max_memory:.2f} GB')
        self.logger.info(f'Total Unified Memory: {self.max_unified_memory:.2f} GB')
        
        # Updated resource requirements for Apple Silicon
        self.model_resource_map = {
            'llama-2-7b': {'memory': 2.0, 'unified_memory': 4.0},
            'llama-2-13b': {'memory': 4.0, 'unified_memory': 8.0},
            'gpt-4': {'memory': 8.0, 'unified_memory': 16.0},
            'default': {'memory': 1.0, 'unified_memory': 2.0}
        }

    def _get_total_memory(self) -> float:
        """
        Get the total system memory.
        """
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)

    def _get_unified_memory(self) -> float:
        """
        Get the total unified memory available on Apple Silicon.
        Uses system_profiler to get accurate unified memory info.
        """
        try:
            import subprocess
            cmd = ["system_profiler", "SPHardwareDataType"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if "Memory:" in line:
                    memory_str = line.split(':')[1].strip()
                    return float(memory_str.split(' ')[0])
            
            self.logger.warning("Couldn't detect unified memory, using system memory instead")
            return self._get_total_memory()
        except Exception as e:
            self.logger.warning(f'Error getting unified memory: {e}')
            return self._get_total_memory()

    def get_available_resources(self) -> Dict[str, Any]:
        """
        Get available system resources specific to Apple Silicon.
        """
        cpu_percent = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory()
        memory_percent = memory_usage.percent
        available_memory = (memory_usage.available / (1024 ** 3))

        # Get GPU/Neural Engine usage via powermetrics if available
        try:
            import subprocess
            cmd = ["sudo", "powermetrics", "--samplers", "gpu_perf", "-n", "1"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            
            gpu_percent = 0
            for line in result.stdout.split('\n'):
                if "GPU Active" in line:
                    gpu_percent = float(line.split(':')[1].strip().replace('%', ''))
        except Exception as e:
            self.logger.debug(f'Could not get GPU metrics: {e}')
            gpu_percent = 0

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'available_memory': available_memory,
            'gpu_percent': gpu_percent,
            'unified_memory': self.max_unified_memory,
            'agents': self.agent_resources
        }

    def can_run_task(self, task_details: Dict[str, Any]) -> bool:
        """
        Check if there are enough resources to run a task on Apple Silicon.
        """
        resource_requirements = task_details.get("resource_requirements", {})
        if not resource_requirements:
            self.logger.info(f"Task {task_details.get('task_id', 'Unknown')} has no resource requirements")
            return True

        model = resource_requirements.get('model', 'default')
        required_resources = self.get_model_resources(model)
        available_resources = self.get_available_resources()

        # Check both system memory and unified memory
        if available_resources['available_memory'] < required_resources['memory']:
            self.logger.warning(
                f"Not enough memory for task {task_details.get('task_id', 'Unknown')}: "
                f"Required {required_resources['memory']:.2f} GB, "
                f"available {available_resources['available_memory']:.2f} GB"
            )
            return False

        if available_resources['unified_memory'] < required_resources['unified_memory']:
            self.logger.warning(
                f"Not enough unified memory for task {task_details.get('task_id', 'Unknown')}: "
                f"Required {required_resources['unified_memory']:.2f} GB, "
                f"available {available_resources['unified_memory']:.2f} GB"
            )
            return False

        self.logger.info(f"Resources available for task {task_details.get('task_id', 'Unknown')}")
        return True

    # The following methods remain largely unchanged
    def track_agent_resource(self, agent_id, resource_usage: Dict[str, Any]):
        self.agent_resources[agent_id] = resource_usage
        self.logger.debug(f"Tracked resources for agent {agent_id}: {resource_usage}")

    def get_agent_resource_usage(self, agent_id: str) -> Dict[str, Any]:
        return self.agent_resources.get(agent_id, {})

    def get_model_resources(self, model_size: str) -> Dict[str, float]:
        return self.model_resource_map.get(model_size, self.model_resource_map.get('default'))

    def check_api_usage(self) -> bool:
        return self.api_count < self.api_limit

    def increment_api_usage(self):
        self.api_count += 1

    def get_status(self) -> Dict[str, Any]:
        return {
            'api_calls_made': self.api_count,
            'max_api_calls': self.api_limit,
            'total_memory': self.max_memory,
            'total_unified_memory': self.max_unified_memory,
            'available_resources': self.get_available_resources(),
            'model_resource_map': self.model_resource_map
        }