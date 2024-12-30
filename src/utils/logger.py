import logging
import sys
from typing import Dict, Any
from src.utils.config import get_config_value

def get_project_logger(config: Dict[str, Any], name: str = 'project', log_level: int = logging.INFO) -> logging.Logger:
    """
    Gets a basic project logger
    """
    logger = logging.getLogger(name) # create new logger if one does not exist
    log_level_str = get_config_value(config, 'log_level', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO) # default to INFO if something is wrong
    logger.setLevel(log_level)
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger