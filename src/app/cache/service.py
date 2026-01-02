from typing import Optional
from src.app.cache.redis import RedisCache
from src.app.cache.keys import make_cache_key


async def get_cached_response(
        user_id: str,
        method: str,
        path: str,
        query_params: dict,
        cache: RedisCache,
        force_refresh: bool = False
) -> tuple[Optional[dict], bool]:
    if force_refresh:
        return None, False
    cache_key = make_cache_key(user_id, method, path, query_params)
    cached_value = await cache.get(cache_key)
    is_hit = False
    if cached_value:
        is_hit = True
    return cached_value, is_hit


async def set_cached_response(
        user_id: str,
        method: str,
        path: str,
        query_params: dict,
        value: dict,
        ttl: int,
        cache: RedisCache,
        resource: str = "tasks"
):
    cache_key = make_cache_key(user_id, method, path, query_params)
    await cache.set(cache_key, value, ttl, user_id, resource)


async def invalidate_user_cache(
        user_id: str,
        cache: RedisCache,
        resource: str = "tasks"
):
    return await cache.invalidate_user_cache(user_id, resource)