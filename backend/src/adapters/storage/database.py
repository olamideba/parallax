from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().async_database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


async def dispose_engine() -> None:
    """Tear down the cached engine and its connection pool.

    The engine is a module-level singleton, but its asyncpg pool is bound to
    whichever event loop was running when it was first created. Celery workers
    call `asyncio.run(...)` once per task, which opens and closes a new loop
    every time — so a cached engine from a prior task's (now-closed) loop
    raises "Future attached to a different loop" on the next task in the same
    worker process. Call this at the end of every Celery task's asyncio.run
    body so the next task creates a fresh engine on its own fresh loop.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


def session_factory() -> sessionmaker:
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory()() as session:
        yield session
