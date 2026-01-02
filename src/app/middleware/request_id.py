import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.app.core.logging import request_id_var, user_id_var
from src.app.core.security import decode_token


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request_id_var.set(request_id)

        credentials = request.headers.get("Authorization")
        if credentials:
            token = credentials.split()[1]
            user_id = decode_token(token).get("sub")
            user_id_var.set(user_id)


        request.state.request_id = request_id

        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000)

        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Response-Time"] = str(duration_ms)

        return response