from core.task_queue import RedisTaskQueue
from core.message_pipeline import HTTPMessagePipeline
from core.resource_manager import ResourceManager 
from agents.architect_agent import ArchitectAgent
from agents.senior_dev_agent import SeniorDevAgent
from agents.junior_dev_agent import JuniorDevAgent
from agents.test_dev_agent import TestDevAgent
from agents.project_manager_agent import ProjectManagerAgent
from utils.config import load_config
from utils.logger import get_project_logger
import time
import threading


if __name__ == "__main__":
    # Load config
    config = load_config()
    # Set up the logger
    logger = get_project_logger(config)

    # Setup Task Queue and Message Pipeline
    redis_host = config.get('redis_host', 'localhost')
    redis_port = config.get('redis_port', 6379)
    task_queue = RedisTaskQueue(host=redis_host, port=redis_port)

    message_pipeline_host = config.get('message_pipeline_host', 'localhost')
    message_pipeline_port = config.get('message_pipeline_port', 8000)
    message_pipeline = HTTPMessagePipeline(host=message_pipeline_host, port=message_pipeline_port, logger=logger)
    message_pipeline.start()

    # Setup Resource Manager
    resource_manager = ResourceManager(config, logger=logger)

    # Setup Agents, pass in the resource manager
    architect = ArchitectAgent(name="Architect", model="gpt-4", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)
    senior_dev = SeniorDevAgent(name="Senior Dev", model="gpt-4", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)
    junior_dev1 = JuniorDevAgent(name="Junior Dev 1", model="llama-2-7b", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)
    junior_dev2 = JuniorDevAgent(name="Junior Dev 2", model="llama-2-7b", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)
    test_dev = TestDevAgent(name="Test Dev", model="llama-2-13b", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)
    project_manager = ProjectManagerAgent(name="Project Manager", model="Qwen2.5-14b", message_pipeline=message_pipeline, task_queue=task_queue, logger=logger)

    # Subscribe agents to message pipeline events
    def handle_task_update(data):
        """
        Print out task updates to the log
        """
        logger.info(f"Task update: {data}")

    message_pipeline.subscribe('task_update', handle_task_update)


    def handle_help_request(data):
        """
        Handle help requests, for now just log it
        """
        logger.warning(f"Help request: {data}")
    message_pipeline.subscribe('request_help', handle_help_request)

     # Scheduler logic
    def scheduler_run():
        """
        Main function for scheduling tasks
        """
        while True:
            # Get pending tasks from the task queue
            pending_tasks = [task for task in task_queue.values() if task['status'] == 'pending']
            for task in pending_tasks:
                if not task['assigned_agent']: # If the task is unassigned
                     # Check if there are enough resources to run the task
                     if resource_manager.can_run_task(task):
                            # Assign based on dependencies and priority
                            if 'dependencies' in task and task['dependencies']:
                                 # check if dependencies are complete, if not skip
                                 deps_complete = True
                                 for dep in task['dependencies']:
                                      dep_task = task_queue.get(dep)
                                      if not dep_task or dep_task['status'] != 'completed':
                                        deps_complete = False
                                        break
                                 if not deps_complete:
                                      logger.debug(f"Skipping task {task['task_id']}, not all dependencies have been resolved.")
                                      continue
                            
                            if task.get('resource_requirements', {}).get('model', '') == 'gpt-4':
                                if resource_manager.can_run_task(task):
                                     if architect.is_active is False:
                                          task['assigned_agent'] = architect.id
                                          architect.start_task(task['task_id'])
                                          task_queue.set(task['task_id'], task)
                                          logger.info(f"Assigned task '{task['task_id']}' to {architect.name}")
                                     elif senior_dev.is_active is False:
                                          task['assigned_agent'] = senior_dev.id
                                          senior_dev.start_task(task['task_id'])
                                          task_queue.set(task['task_id'], task)
                                          logger.info(f"Assigned task '{task['task_id']}' to {senior_dev.name}")
                                     else:
                                          logger.debug(f"Skipping task {task['task_id']}, gpt-4 agent active")
                                else:
                                      logger.info(f"Skipping task {task['task_id']}, not enough resources for gpt-4")
                            elif task.get('resource_requirements', {}).get('model', '').startswith('llama'):
                                if junior_dev1.is_active is False:
                                     task['assigned_agent'] = junior_dev1.id
                                     junior_dev1.start_task(task['task_id'])
                                     task_queue.set(task['task_id'], task)
                                     logger.info(f"Assigned task '{task['task_id']}' to {junior_dev1.name}")
                                elif junior_dev2.is_active is False:
                                     task['assigned_agent'] = junior_dev2.id
                                     junior_dev2.start_task(task['task_id'])
                                     task_queue.set(task['task_id'], task)
                                     logger.info(f"Assigned task '{task['task_id']}' to {junior_dev2.name}")
                                else:
                                      logger.debug(f"Skipping task {task['task_id']}, llama agent active")
                            else:
                                 if test_dev.is_active is False:
                                      task['assigned_agent'] = test_dev.id
                                      test_dev.start_task(task['task_id'])
                                      task_queue.set(task['task_id'], task)
                                      logger.info(f"Assigned task '{task['task_id']}' to {test_dev.name}")
                                 else:
                                     logger.debug(f"Skipping task {task['task_id']}, test dev active")
                     else:
                          logger.info(f"Skipping task {task['task_id']}, not enough resources")

            time.sleep(1)
    # Start the scheduler in its own thread
    scheduler_thread = threading.Thread(target=scheduler_run)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Start Agents
    agents = [architect, senior_dev, junior_dev1, junior_dev2, test_dev]
    for agent in agents:
        agent_thread = threading.Thread(target=agent.run)
        agent_thread.daemon = True # so that threads close on program close
        agent_thread.start()

    # Example seed task
    task_queue.set('task-0', {
        'task_id': 'task-0',
        'description': 'Create a basic python script that prints "Hello, World!"',
        'dependencies': [],
        'status': 'pending',
        'assigned_agent': None,
        'priority': 1,
        'resource_requirements': {
            'model': 'gpt-4'
        }
    })


    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        message_pipeline.stop()