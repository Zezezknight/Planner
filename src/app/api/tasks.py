from __future__ import annotations

import logging
from datetime import date as date_cls
from typing import Optional
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response

from src.app.core.deps import get_current_user, get_tasks_repo, get_cache_service
from src.app.db.repositories import TasksRepository
from src.app.models.tasks import TaskCreate, TaskOut, TaskUpdate
from src.app.cache.service import get_cached_response, set_cached_response, invalidate_user_cache
from src.app.core.config import settings


router = APIRouter()
logger = logging.getLogger("api")


@router.post("",
             status_code=status.HTTP_201_CREATED,
             response_model=TaskOut)
async def create_task(
    request: Request,
    payload: TaskCreate,
    tasks: TasksRepository = Depends(get_tasks_repo),
    cache=Depends(get_cache_service),
    user=Depends(get_current_user),
):
    payload = payload.model_dump()
    created_task = await tasks.create(user['id'], payload)

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("Task created, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 201,
    })
    return TaskOut.model_validate(created_task)


@router.get("",
            response_model=list[TaskOut])
async def list_tasks(
    response: Response,
    request: Request,
    tasks: TasksRepository = Depends(get_tasks_repo),
    user=Depends(get_current_user),
    date: Optional[date_cls] = Query(default=None),
    type: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    cache=Depends(get_cache_service)
):
    response.headers['X-Cache'] = 'MISS'

    if request.headers.get('cache-control') == 'no-cache':
        result = await tasks.list(user['id'], date_eq=date, type_eq=type, q=q)
        return [TaskOut.model_validate(task) for task in result]

    query_params = dict()
    if date:
        query_params['date'] = date
    if type:
        query_params['type'] = type
    if q:
        query_params['q'] = q

    method = request.method
    path = request.url.path
    cached_response, is_hit = await get_cached_response(user["id"], method, path, query_params, cache=cache)

    if is_hit:
        response.headers['X-Cache'] = 'HIT'
        result = [TaskOut.model_validate(task) for task in cached_response]
        return result

    result = await tasks.list(user['id'], date_eq=date, type_eq=type, q=q)

    await set_cached_response(user["id"], method, path, query_params, result, settings.CACHE_TTL_TASKS, cache=cache)

    logger.info("Request completed", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 200,
    })
    return [TaskOut.model_validate(task) for task in result]


@router.get("/{task_id}",
            response_model=TaskOut)
async def get_task(
        task_id: str,
        tasks: TasksRepository = Depends(get_tasks_repo),
        user=Depends(get_current_user)
):
    try:
        ObjectId(task_id)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=404, detail='Task is not found')

    result = await tasks.get(task_id)

    if not result:
        raise HTTPException(status_code=404, detail='Task is not found')
    if result['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail='Access denied')

    return TaskOut.model_validate(result)


@router.patch("/{task_id}",
              response_model=TaskOut)
async def update_task(
    request: Request,
    task_id: str,
    patch: TaskUpdate,
    tasks: TasksRepository = Depends(get_tasks_repo),
    cache=Depends(get_cache_service),
    user=Depends(get_current_user),
):
    check_task = await tasks.get(task_id)

    if not check_task:
        raise HTTPException(status_code=404, detail='Task is not found')
    if check_task['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail='Access denied')

    new_info = patch.model_dump()
    payload = dict()
    for key in new_info.keys():
        if new_info.get(key):
            payload[key] = new_info.get(key)

    result = await tasks.update(task_id, payload)

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("Task updated, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 200,
    })
    return TaskOut.model_validate(result)


@router.delete("/{task_id}",
               status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
        request: Request,
        task_id: str,
        tasks: TasksRepository = Depends(get_tasks_repo),
        cache=Depends(get_cache_service),
        user=Depends(get_current_user)):
    check_task = await tasks.get(task_id)

    if not check_task:
        raise HTTPException(status_code=404, detail='Task is not found')
    if check_task['user_id'] != user['id']:
        raise HTTPException(status_code=403, detail='Access denied')

    await tasks.delete(task_id)

    await invalidate_user_cache(user["id"], resource="tasks", cache=cache)

    logger.info("Task deleted, cache invalidated", extra={
        "method": request.method,
        "path": request.url.path,
        "status": 204,
    })