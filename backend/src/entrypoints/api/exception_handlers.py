from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions.base import IngestionError, NotFoundError, ParallaxError
from src.entrypoints.api.schemas import problem_response
from src.shared.logging import logger


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return problem_response(
            status_code=exc.status_code,
            detail=detail,
            request_path=str(request.url.path),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return problem_response(
            status_code=exc.status_code,
            detail=detail,
            request_path=str(request.url.path),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = [
            {"pointer": "/".join(str(p) for p in err["loc"]), "detail": err["msg"]}
            for err in exc.errors()
        ]
        return problem_response(
            status_code=422,
            title="Unprocessable Content",
            detail="Request validation failed",
            request_path=str(request.url.path),
            type_="/problems/validation-error",
            errors=errors,
        )

    @app.exception_handler(NotFoundError)
    async def not_found_error_handler(request: Request, exc: NotFoundError):
        return problem_response(
            status_code=404,
            detail=exc.message,
            request_path=str(request.url.path),
        )

    @app.exception_handler(IngestionError)
    async def ingestion_error_handler(request: Request, exc: IngestionError):
        return problem_response(
            status_code=422,
            detail=exc.message,
            request_path=str(request.url.path),
            type_="/problems/ingestion-error",
        )

    @app.exception_handler(ParallaxError)
    async def parallax_error_handler(request: Request, exc: ParallaxError):
        return problem_response(
            status_code=400,
            detail=exc.message,
            request_path=str(request.url.path),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return problem_response(
            status_code=500,
            detail="Internal server error",
            request_path=str(request.url.path),
            type_="/problems/internal-server-error",
        )
