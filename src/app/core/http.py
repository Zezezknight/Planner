import httpx
from src.app.core.config import settings


def create_http_client(request_id: str = None) -> httpx.AsyncClient:
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

