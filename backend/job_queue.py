import os
from typing import Optional

import redis


DEFAULT_REDIS_URL = "redis://127.0.0.1:6379/0"
DEFAULT_QUEUE_KEY = "startup_builder:jobs:queue"


class RedisJobQueue:
    def __init__(self, redis_url: Optional[str] = None, queue_key: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
        self.queue_key = queue_key or os.getenv("REDIS_JOB_QUEUE_KEY", DEFAULT_QUEUE_KEY)
        self._client = redis.Redis.from_url(self.redis_url, decode_responses=True)

    def is_available(self) -> bool:
        try:
            return bool(self._client.ping())
        except redis.RedisError:
            return False

    def enqueue(self, job_id: str) -> None:
        self._client.rpush(self.queue_key, job_id)

    def enqueue_many(self, job_ids: list[str]) -> None:
        if not job_ids:
            return
        self._client.rpush(self.queue_key, *job_ids)

    def dequeue(self, timeout: int = 5) -> Optional[str]:
        payload = self._client.blpop(self.queue_key, timeout=timeout)
        if not payload:
            return None
        return payload[1]
