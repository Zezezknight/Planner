from __future__ import annotations

import httpx
import redis.asyncio as aioredis
from typing import Annotated, Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.app.cache.redis import RedisCache
from src.app.core.logging import request_id_var
from src.app.core.security import decode_token
from src.app.db.repositories import UsersRepository, TasksRepository, MotorTasksRepository, MotorUsersRepository
from src.app.core.config import settings
from src.app.external.nager import NagerImporter
from src.app.external.weather_open_meteo import WeatherImporter
from src.app.external.news_spaceflight import NewsImporter

bearer_scheme = HTTPBearer(auto_error=False)

_mongo_client: AsyncIOMotorClient | None = None
_redis_pool: aioredis.ConnectionPool | None = None

async def init_dependencies():
    global _mongo_client, _redis_pool

    # MongoDB
    _mongo_client = AsyncIOMotorClient(
        settings.MONGO_URI,
        maxPoolSize=settings.MONGO_POOL_SIZE
    )
    db = _mongo_client[settings.MONGO_DB_NAME]
    await db["users"].create_index("email", unique=True)
    await db["tasks"].create_index([("user_id", 1), ("date", 1)])
    await db["tasks"].create_index([("user_id", 1), ("type", 1)])
    await db["tasks"].create_index([("user_id", 1), ("meta.source_id", 1)], unique=True,
                                   partialFilterExpression={"meta.source_id": {"$exists": True, "$type": 'string'}})

    # Redis
    _redis_pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_POOL_SIZE
    )


async def close_dependencies():
    global _mongo_client, _redis_pool

    if _mongo_client:
        _mongo_client.close()

    if _redis_pool:
        await _redis_pool.aclose()


async def get_mongo_client() -> AsyncIOMotorClient:
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized")
    return _mongo_client


async def get_mongo_db(
        client: Annotated[AsyncIOMotorClient, Depends(get_mongo_client)]
) -> AsyncIOMotorDatabase:
    return client[settings.MONGO_DB_NAME]


async def get_redis_client() -> aioredis.Redis:
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialized")
    return aioredis.Redis(connection_pool=_redis_pool)


async def get_http_client() -> httpx.AsyncClient:
    request_id = request_id_var.get("system")

    headers = {"Accept": "application/json"}
    if request_id:
        headers["X-Request-ID"] = request_id

    return httpx.AsyncClient(
        timeout=settings.HTTP_TIMEOUT,
        limits=httpx.Limits(
            max_connections=settings.HTTP_MAX_CONNECTIONS,
            max_keepalive_connections=5
        ),
        headers=headers
    )


async def get_tasks_repo(
        db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
) -> TasksRepository:
    return MotorTasksRepository(db["tasks"])


async def get_users_repo(
        db: Annotated[AsyncIOMotorDatabase, Depends(get_mongo_db)]
) -> UsersRepository:
    return MotorUsersRepository(db["users"])


async def get_cache_service(
        redis: Annotated[aioredis.Redis, Depends(get_redis_client)]
) -> RedisCache:
    return RedisCache(redis)


async def get_nager_importer(
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
) -> NagerImporter:
    return NagerImporter(http_client)


async def get_weather_importer(
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
) -> WeatherImporter:
    return WeatherImporter(http_client)


async def get_news_importer(
        http_client: Annotated[httpx.AsyncClient, Depends(get_http_client)]
) -> NewsImporter:
    return NewsImporter(http_client)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    users: Annotated[UsersRepository, Depends(get_users_repo)],
):
    if not credentials:
        raise HTTPException(status_code=401, detail='Not authenticated')
    token = credentials.credentials
    payload = decode_token(token)
    current_user = await users.get_by_id(payload.get('sub'))
    return current_user
