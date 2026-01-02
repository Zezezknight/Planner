from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, JSONResponse

from src.app.api.auth import router as auth_router
from src.app.api.importers import router as import_router
from src.app.api.tasks import router as tasks_router
from src.app.core.config import settings
from src.app.core.deps import init_dependencies, close_dependencies
from src.app.middleware.request_id import RequestTracingMiddleware
from src.app.core.logging import init_logging, stop_logging
from src.app.services.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_dependencies()
    init_logging()
    logging.info("Application started")
    if settings.SCHEDULER_ENABLED:
        scheduler.start()
    yield

    # Shutdown
    if settings.SCHEDULER_ENABLED:
        scheduler.shutdown()
    await close_dependencies()
    stop_logging()


app = FastAPI(
    title="Student Planner API",
    version="0.2.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    lifespan=lifespan
)


@app.exception_handler(Exception)
async def logging_exception(request: Request, exc: Exception):
    logging.getLogger("api").error(str(exc), extra={
        "method": request.method,
        "path": request.url.path,
        "status": 500
    }, exc_info=True)
    return JSONResponse(status_code=500, content="Internal server error")


app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestTracingMiddleware)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(import_router, prefix="/import", tags=["import"])

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@app.get("/ui/tasks", response_class=HTMLResponse, tags=["ui"])
async def ui_tasks():
    html = """<!doctype html><html lang="ru"><head>
      <meta charset="utf-8" />
      <title>Мои задачи — Студенческий планировщик</title>
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <style>body{font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;margin:2rem}
      table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:.5rem}</style>
    </head><body>
      <h1>Мои задачи</h1>
      <p>Откройте DevTools и выполните авторизацию через API, затем <code>GET /tasks</code>.</p>
    </body></html>"""
    return HTMLResponse(html)
