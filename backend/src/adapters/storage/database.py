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


def _session_factory() -> sessionmaker:
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _session_factory()() as session:
        yield session
