"""
Database session management.

Supports both SQLite (local/test) and PostgreSQL (production) through
SQLAlchemy's async engine. The dialect is determined entirely by DATABASE_URL
so the same codebase works in both environments.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

logger = logging.getLogger(__name__)

# These are set during init_db() so tests can override them
_engine = None
_session_factory = None


async def init_db() -> None:
    """Create the async engine and session factory, then ensure tables exist."""
    global _engine, _session_factory

    settings = get_settings()
    url = settings.database_url

    # SQLite needs special connect args for async
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    _engine = create_async_engine(
        url,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables from models (import here to avoid circular deps)
    from app.db.models import Base

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database engine created for %s", url.split("@")[-1] if "@" in url else url)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the active sessionmaker factory."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for dependency injection."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_db() -> None:
    """Dispose the engine on shutdown."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
