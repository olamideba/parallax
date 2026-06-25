from __future__ import annotations

import time
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.config import get_settings
from src.shared.logging import logger

_SKIP_PATHS = {"/docs", "/redoc", "/openapi.json", "/"}


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = f"PX-{uuid.uuid4().hex[:12]}"
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        rid = getattr(request.state, "request_id", "-")
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "-"
        )
        status = response.status_code
        parts = [
            f"{request.method} {request.url.path} {status} {duration_ms:.1f}ms",
            f"rid={rid}",
            f"ip={ip}",
        ]
        level = "WARNING" if status >= 400 else "INFO"
        logger.log(level, " | ".join(parts))
        return response


def init_middlewares(app: FastAPI) -> None:
    settings = get_settings()
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o) for o in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
