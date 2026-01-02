import json
import logging
from json import JSONDecodeError
from typing import Optional
import redis.asyncio as aioredis
from redis import RedisError
from src.app.core.config import settings
from src.app.cache.keys import make_cache_index_key


logger = logging.getLogger("cache")


class RedisCache:

    def __init__(self, client: aioredis.Redis):
        self.client = client

    async def get(self, key: str) -> Optional[dict]:
        try:
            data = await self.client.get(key)
            return json.loads(data)
        except (RedisError, JSONDecodeError, TypeError, AttributeError):
            pass

    async def set(self, key: str, value: dict, ttl: int, user_id: str, resource: str = "tasks"):
        try:
            data_to_cache = json.dumps(value)
            data_size = len(data_to_cache.encode("utf-8"))
            if data_size > settings.CACHE_MAX_BYTES:
                return
            await self.client.set(key, json.dumps(value), ex=ttl)

            index_key = make_cache_index_key(user_id, resource)
            await self.client.sadd(index_key, key)
            await self.client.expire(index_key, ttl)
        except (RedisError, AttributeError, TypeError):
            pass

    async def invalidate_user_cache(self, user_id: str, resource: str = "tasks"):
        index_key = make_cache_index_key(user_id, resource)
        try:
            cache_keys = await self.client.smembers(index_key)
            async with self.client.pipeline() as pipe:
                if cache_keys:
                    await pipe.delete(*cache_keys)
                await pipe.delete(index_key)
                await pipe.execute()
            return
        except Exception:
            logger.error(f"Failed to invalidate cache for user {user_id}", exc_info=True)
            return
