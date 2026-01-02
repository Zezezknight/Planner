from __future__ import annotations

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.app.cache.redis import RedisCache
from src.app.core.deps import (
    get_tasks_repo,
    get_nager_importer,
    get_weather_importer,
    get_news_importer,
    get_current_user,
    get_cache_service
)
from src.app.db.repositories import TasksRepository
from src.app.external.nager import NagerImporter
from src.app.external.weather_open_meteo import WeatherImporter
from src.app.external.news_spaceflight import NewsImporter
from src.app.models.tasks import WeatherImportRequest, ImportResult, NewsImportRequest
import httpx
from src.app.services.import_service import execute_import
from src.app.cache.service import invalidate_user_cache


router = APIRouter()
logger = logging.getLogger("api")


@router.post("/nager",
             response_model=ImportResult)
async def import_nager(
    request: Request,
    country: Annotated[str, Query(min_length=2, max_length=2, description="ISO-2")],
    year: Annotated[int, Query(ge=1900, le=2100)],
    tasks: TasksRepository = Depends(get_tasks_repo),
    importer: NagerImporter = Depends(get_nager_importer),
    cache: RedisCache = Depends(get_cache_service),
    user=Depends(get_current_user),
):
    try:
        import_result = await execute_import(importer, user['id'], tasks,
                                      fetch_kwargs={
                                          "year": year,
                                          "country": country,
                                          "request_id": request.state.request_id
                                      },
                                      normalize_kwargs={
                                          "country": country
                                      })
    except RuntimeError:
        raise HTTPException(status_code=502, detail='Nager.Date unavailable')
    except httpx.TimeoutException:
        raise HTTPException(status_code=502, detail='Service unavailable')
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            raise HTTPException(status_code=502, detail='Service unavailable')
        raise HTTPException(status_code=400, detail='Bad Request')

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("Nager imported, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 200,
    })
    return import_result


@router.post("/weather",
             response_model=ImportResult)
async def import_weather(
    request: Request,
    request_body: WeatherImportRequest,
    tasks: TasksRepository = Depends(get_tasks_repo),
    importer: WeatherImporter = Depends(get_weather_importer),
    cache: RedisCache = Depends(get_cache_service),
    user=Depends(get_current_user),
):
    lat = request_body.lat
    lon = request_body.lon
    days = request_body.days
    hot_from = request_body.hot_from
    cold_to = request_body.cold_to
    try:
        import_result = await execute_import(importer, user['id'], tasks,
                                      fetch_kwargs={
                                          "lat": lat,
                                          "lon": lon,
                                          "days": days,
                                          "request_id": request.state.request_id
                                      },
                                      normalize_kwargs={"lat": lat, "lon": lon, "hot_from": hot_from, "cold_to": cold_to})
    except httpx.TimeoutException:
        raise HTTPException(status_code=502, detail='Service unavailable')
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            raise HTTPException(status_code=502, detail='Service unavailable')
        raise HTTPException(status_code=400, detail='Bad Request')
    except RuntimeError:
        raise HTTPException(status_code=502, detail='OpenMeteo unavailable')

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("Weather imported, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 200,
    })
    return import_result



@router.post("/news",
             response_model=ImportResult)
async def import_news(
    request: Request,
    request_body: NewsImportRequest,
    tasks: TasksRepository = Depends(get_tasks_repo),
    importer: NewsImporter = Depends(get_news_importer),
    cache: RedisCache = Depends(get_cache_service),
    user=Depends(get_current_user),
):
    try:
        imported_result = await execute_import(importer, user['id'], tasks,
                                      fetch_kwargs={
                                          "q": request_body.q,
                                          "from_date": request_body.from_date,
                                          "limit": request_body.limit,
                                          "request_id": request.state.request_id
                                      },
                                      normalize_kwargs={})
    except httpx.TimeoutException:
        raise HTTPException(status_code=502, detail='Service unavailable')
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            raise HTTPException(status_code=502, detail='Service unavailable')
        raise HTTPException(status_code=400, detail='Bad Request')
    except RuntimeError:
        raise HTTPException(status_code=502, detail='SpaceflightNews unavailable')

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("News imported, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 200,
    })
    return imported_result
