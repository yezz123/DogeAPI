"""Async SQLAlchemy engine and session factory.

We expose:

- ``engine`` &mdash; the lazily-built process-wide async engine
- ``async_session_factory`` &mdash; the async sessionmaker
- ``get_session`` &mdash; FastAPI dependency yielding an :class:`AsyncSession`
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from dogeapi.settings import Settings, get_settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Build the async engine once per process."""
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency for an async DB session.

    Sessions are scoped per request; they commit on clean exit and roll
    back on any exception.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def reset_engine_for_settings(_settings: Settings) -> None:
    """Drop the cached engine so the next call rebuilds with new settings.

    Tests that change ``DATABASE_URL`` between fixtures need this.
    """
    get_engine.cache_clear()
    get_session_factory.cache_clear()
