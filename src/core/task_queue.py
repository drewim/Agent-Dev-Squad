import redis
import json
from typing import Dict, Any

class RedisTaskQueue:
    """
    Task queue using Redis.
    """
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db)

    def set(self, task_id: str, task_details: Dict[str, Any]):
        """
        Adds/updates a task in the queue.
        """
        self.redis.set(task_id, json.dumps(task_details))

    def get(self, task_id: str) -> Dict[str, Any] | None:
         """
         Gets a task from the queue
         """
         task_str = self.redis.get(task_id)
         if task_str:
             return json.loads(task_str)
         return None

    def values(self):
        """
        Returns all of the tasks in the queue.
        """
        all_keys = self.redis.keys('*')
        all_values = []
        for key in all_keys:
            task = self.get(key.decode('utf-8')) # need to decode the key
            if task:
                 all_values.append(task)
        return all_values

    def delete(self, task_id: str):
        """
        Removes a task from the queue.
        """
        self.redis.delete(task_id)

    def clear_all(self):
        """
        Clear all tasks in the queue
        """
        self.redis.flushdb()

    def __len__(self):
        return len(self.redis.keys('*'))