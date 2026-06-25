from __future__ import annotations

from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

DataType = TypeVar("DataType")


class GlobalResponse(BaseModel, Generic[DataType]):
    success: bool = True
    data: DataType | None = None
    message: str


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    success: bool = False
    instance: str | None = None
    errors: list[dict[str, Any]] | None = None


def problem_response(
    status_code: int,
    detail: str,
    request_path: str,
    title: str | None = None,
    type_: str = "about:blank",
    errors: list[dict[str, Any]] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    body = ProblemDetails(
        type=type_,
        title=title or _default_title(status_code),
        status=status_code,
        detail=detail,
        instance=request_path,
        errors=errors,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(exclude_none=True),
        headers=headers,
    )


def _default_title(status_code: int) -> str:
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        422: "Unprocessable Content",
        500: "Internal Server Error",
    }
    return titles.get(status_code, "Error")
