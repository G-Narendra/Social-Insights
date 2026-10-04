"""
Service layer for Collection Runs.
Manages run lifecycle, concurrency protection, and per-source telemetry.
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CollectionRun


async def create_collection_run(
    session: AsyncSession,
    keyword_id: int,
    requested_limit: int = 100,
) -> CollectionRun:
    """Create a new collection run in queued status."""
    run = CollectionRun(
        keyword_id=keyword_id,
        status="queued",
        started_at=datetime.datetime.now(datetime.UTC),
        requested_limit=requested_limit,
        per_source={},
        errors=[],
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_active_run_for_keyword(
    session: AsyncSession,
    keyword_id: int,
) -> CollectionRun | None:
    """Check if an active run (queued or running) already exists for this keyword."""
    query = select(CollectionRun).where(
        CollectionRun.keyword_id == keyword_id,
        CollectionRun.status.in_(["queued", "running"]),
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_run_by_id(
    session: AsyncSession,
    run_id: int,
) -> CollectionRun | None:
    """Fetch run status and diagnostics by run ID."""
    return await session.get(CollectionRun, run_id)


async def update_run_status(
    session: AsyncSession,
    run_id: int,
    status: str,
    per_source: dict[str, Any] | None = None,
    errors: list[Any] | None = None,
) -> None:
    """Update execution state, source breakdown, and error list."""
    run = await session.get(CollectionRun, run_id)
    if run:
        run.status = status
        if per_source is not None:
            run.per_source = per_source
        if errors is not None:
            run.errors = errors
        if status in ["succeeded", "failed", "partial"]:
            run.finished_at = datetime.datetime.now(datetime.UTC)
        await session.commit()
