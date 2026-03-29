import redis
import json
from typing import Any, Optional
from backend.core.config import settings
from backend.utils.logger import logger

class CacheService:
    def __init__(self):
        try:
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            self.client.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    def set_data(self, key: str, data: Any, ttl_seconds: int = 300):
        if not self.client:
            return
        try:
            self.client.setex(key, ttl_seconds, json.dumps(data))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    def get_data(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            cached = self.client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
        return None

cache_service = CacheService()
