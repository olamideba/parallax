from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from src.config import get_settings
from src.entrypoints.api.exception_handlers import register_exception_handlers
from src.entrypoints.api.middlewares import init_middlewares
from src.entrypoints.api.schemas import GlobalResponse
from src.entrypoints.api.v1.router import router as v1_router
from src.shared.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Parallax API",
        description="Agent society for faculty outreach triage",
        version="0.1.0",
        lifespan=lifespan,
    )
    init_middlewares(app)
    register_exception_handlers(app)

    versioned = APIRouter(prefix=settings.API_V1_PREFIX)
    versioned.include_router(v1_router)
    app.include_router(versioned)

    @app.get("/", tags=["root"])
    async def root() -> GlobalResponse[dict]:
        return GlobalResponse(message="Parallax API", data={"docs": "/docs"})

    @app.get("/health", tags=["health"])
    async def health() -> GlobalResponse[dict]:
        return GlobalResponse(message="OK", data={"status": "healthy"})

    return app


app = create_app()
