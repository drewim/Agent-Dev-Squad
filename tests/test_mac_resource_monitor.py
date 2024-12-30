# Standard library imports
# import os
# import sys
import time

from src.core.mac_resource_manager import MacResourceManager
# from utils.config import get_config_value


def test_resource_monitoring():
    # Set up basic configuration
    config = {
        'api_limit': 10,
        'log_level': 'DEBUG'
    }
    
    # Initialize the resource manager
    manager = MacResourceManager(config)
    
    print("\n=== Basic System Information ===")
    print(f"Total System Memory: {manager.max_memory:.2f} GB")
    print(f"Total Unified Memory: {manager.max_unified_memory:.2f} GB")
    
    # Test resource monitoring over a short period
    print("\n=== Resource Monitoring Test ===")
    for i in range(3):
        resources = manager.get_available_resources()
        print(f"\nSample {i + 1}:")
        print(f"CPU Usage: {resources['cpu_percent']}%")
        print(f"Memory Usage: {resources['memory_percent']}%")
        print(f"Available Memory: {resources['available_memory']:.2f} GB")
        print(f"GPU Usage: {resources['gpu_percent']}%")
        time.sleep(2)  # Wait 2 seconds between measurements
    
    # Test task resource checking
    print("\n=== Task Resource Check Test ===")
    test_tasks = [
        {
            "task_id": "small_task",
            "resource_requirements": {
                "model": "llama-2-7b"
            }
        },
        {
            "task_id": "large_task",
            "resource_requirements": {
                "model": "gpt-4"
            }
        }
    ]
    
    for task in test_tasks:
        can_run = manager.can_run_task(task)
        print(f"\nTask: {task['task_id']}")
        print(f"Model: {task['resource_requirements']['model']}")
        print(f"Can run: {'Yes' if can_run else 'No'}")
    
    # Test API usage tracking
    print("\n=== API Usage Test ===")
    print(f"Initial API calls: {manager.api_count}")
    manager.increment_api_usage()
    manager.increment_api_usage()
    print(f"After 2 API calls: {manager.api_count}")
    print(f"API calls available: {'Yes' if manager.check_api_usage() else 'No'}")
    
    # Get final status
    print("\n=== Final System Status ===")
    status = manager.get_status()
    print(f"API Calls Made: {status['api_calls_made']}")
    print(f"Total Memory: {status['total_memory']:.2f} GB")
    print(f"Total Unified Memory: {status['total_unified_memory']:.2f} GB")
    
    # Test agent resource tracking
    print("\n=== Agent Resource Tracking Test ===")
    test_agent_resources = {
        "memory_usage": 1.5,
        "unified_memory_usage": 2.0,
        "cpu_usage": 25.0
    }
    manager.track_agent_resource("test_agent_1", test_agent_resources)
    agent_resources = manager.get_agent_resource_usage("test_agent_1")
    print(f"Test Agent Resources: {agent_resources}")


if __name__ == "__main__":
    try:
        test_resource_monitoring()
    except Exception as e:
        print(f"Error during testing: {e}")