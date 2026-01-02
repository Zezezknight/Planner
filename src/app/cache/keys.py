import hashlib
from src.app.core.config import settings


def make_cache_key(user_id, method, path, query_params: dict):
    sorted_params = sorted(query_params.items())
    request_str = "&".join(f"{key}={value}" for key, value in sorted_params)
    query_hash = hashlib.sha256(request_str.encode()).hexdigest()[:16]
    return f"cache:{settings.APP_ENV}:{user_id}:{method}:{path}:{query_hash}"


def make_cache_index_key(user_id, resource: str = "tasks"):
    return f"cache_index:{settings.APP_ENV}:{user_id}:{resource}"
