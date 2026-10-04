"""
Internal API router for automated scheduled ingestion (BON-05).
Protected by shared secret header (X-Internal-Secret).
Invoked periodically via GitHub Actions cron or external scheduler.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, verify_internal_secret
from app.db.models import Keyword
from app.services.collection_job import execute_collection_pipeline
from app.services.run_service import create_collection_run, get_active_run_for_keyword

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post(
    "/ingest",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_internal_secret)],
)
async def run_scheduled_ingestion(
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Trigger scheduled ingestion across all active tracked keywords.
    Protected by shared secret header. Keeps free instances warm.
    """
    query = select(Keyword).where(Keyword.is_tracked.is_(True))
    result = await session.execute(query)
    keywords = list(result.scalars().all())

    triggered = []
    skipped = []

    for kw in keywords:
        # Avoid duplicate runs if already active
        active = await get_active_run_for_keyword(session, kw.id)
        if active:
            skipped.append(kw.term)
            continue

        run = await create_collection_run(session, keyword_id=kw.id, requested_limit=50)
        background_tasks.add_task(
            execute_collection_pipeline,
            keyword_id=kw.id,
            run_id=run.id,
            keyword_term=kw.term,
            sources=None,  # All enabled sources
            limit=50,
            aliases=kw.aliases,
            context_hint=kw.context_hint,
        )
        triggered.append({"keyword": kw.term, "run_id": run.id})

    logger.info(
        "Internal scheduled ingestion: triggered=%d, skipped=%d", len(triggered), len(skipped)
    )
    return {
        "status": "success",
        "triggered_count": len(triggered),
        "triggered": triggered,
        "skipped": skipped,
    }
