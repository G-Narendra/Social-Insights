"""
Database session management.

Supports both SQLite (local/test) and PostgreSQL (production) through
SQLAlchemy's async engine. The dialect is determined entirely by DATABASE_URL
so the same codebase works in both environments.
"""

from __future__ import annotations

import logging
import urllib.parse
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

logger = logging.getLogger(__name__)

# These are set during init_db() so tests can override them
_engine = None
_session_factory = None


def normalize_database_connection(raw_url: str) -> tuple[str, dict[str, Any]]:
    """
    Sanitize and adapt database URLs for async SQLAlchemy.
    - Configures check_same_thread=False for SQLite.
    - Normalizes postgres:// and postgresql:// prefixes to postgresql+asyncpg://.
    - Strips 'sslmode' and 'ssl' query parameters from PostgreSQL URLs and maps them
      cleanly into connect_args['ssl'] to prevent:
      'TypeError: connect() got an unexpected keyword argument sslmode' in asyncpg.
    - Automatically enables SSL for remote managed databases (e.g. Neon, Supabase, RDS).
    """
    connect_args: dict[str, Any] = {}

    if raw_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return raw_url, connect_args

    url = raw_url
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]

    parsed = urllib.parse.urlsplit(url)
    query_params = urllib.parse.parse_qs(parsed.query)

    ssl_setting = None
    if "sslmode" in query_params:
        ssl_setting = query_params.pop("sslmode")[0]
    if "ssl" in query_params:
        ssl_setting = query_params.pop("ssl")[0]

    hostname = (parsed.hostname or "").lower()
    is_local = hostname in ("localhost", "127.0.0.1", "0.0.0.0", "db")

    if ssl_setting is not None:
        if ssl_setting.lower() in ("disable", "false", "0", "none"):
            connect_args["ssl"] = False
        else:
            connect_args["ssl"] = "require"
    elif not is_local:
        connect_args["ssl"] = "require"

    new_query = urllib.parse.urlencode(query_params, doseq=True)
    clean_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment)
    )
    return clean_url, connect_args


async def init_db() -> None:
    """Create the async engine and session factory, then ensure tables exist."""
    global _engine, _session_factory

    settings = get_settings()
    clean_url, connect_args = normalize_database_connection(settings.database_url)

    _engine = create_async_engine(
        clean_url,
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

    logger.info("Database engine created for %s", clean_url.split("@")[-1] if "@" in clean_url else clean_url)


def set_session_factory(factory: async_sessionmaker[AsyncSession] | None) -> None:
    """Set or clear the active sessionmaker factory (useful for testing and background tasks)."""
    global _session_factory
    _session_factory = factory


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
