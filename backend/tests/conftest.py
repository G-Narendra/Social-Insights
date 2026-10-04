"""
Shared test fixtures for the Social Insights test suite.

Provides an isolated in-memory database for each test, ensuring tests
never affect each other and never hit the real database.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated in-memory SQLite session per test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with factory() as session:
        yield session

    await engine.dispose()
