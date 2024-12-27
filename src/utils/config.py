# import os
from typing import Dict, Any
import json

def load_config(config_file="config.json") -> Dict[str, Any]:
     """
     Loads the config.json file, if there is an error reading/parsing file, then returns a blank dictionary
     """
     try:
         with open(config_file, "r") as f:
             config = json.load(f)
         return config
     except (FileNotFoundError, json.JSONDecodeError) as e:
         print("Error: could not load config, returning blank config")
         return {}

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Gets the value associated with a specific key in a config dict, returns the default value if not found.
    """
    return config.get(key, default)

# Example config.json
# {
#     "redis_host": "localhost",
#     "redis_port": 6379,
#     "message_pipeline_host": "localhost",
#     "message_pipeline_port": 8000,
#      "log_level": "DEBUG",
#      "api_limit": 10
# }