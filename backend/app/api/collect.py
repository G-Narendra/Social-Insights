"""
API router for Data Collection initiation and run status polling.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import enforce_rate_limit, get_db, require_role
from app.db.models import User
from app.schemas.runs import CollectionRunResponse, CollectRequest
from app.services.collection_job import execute_collection_pipeline
from app.services.keyword_service import get_or_create_keyword
from app.services.run_service import (
    create_collection_run,
    get_active_run_for_keyword,
    get_run_by_id,
)

router = APIRouter(prefix="/api", tags=["collection"])


@router.post(
    "/collect",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(enforce_rate_limit(max_requests=15, window_seconds=60))],
)
async def trigger_collection(
    payload: CollectRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin", "analyst"]))],
) -> dict:
    """
    Initiate an asynchronous collection run for a keyword.
    Idempotent: if a run is already queued or running for this keyword,
    returns the existing active run_id.
    """
    keyword = await get_or_create_keyword(session, term=payload.keyword)

    # Idempotency check: check if a collection is already active
    active_run = await get_active_run_for_keyword(session, keyword_id=keyword.id)
    if active_run:
        return {
            "run_id": active_run.id,
            "keyword_id": keyword.id,
            "keyword": keyword.term,
            "status": active_run.status,
            "message": "Collection run already in progress for this keyword.",
        }

    # Create new run
    run = await create_collection_run(
        session=session,
        keyword_id=keyword.id,
        requested_limit=payload.limit or 100,
    )

    # Spawn background worker task
    background_tasks.add_task(
        execute_collection_pipeline,
        keyword_id=keyword.id,
        run_id=run.id,
        keyword_term=keyword.term,
        sources=payload.sources,
        limit=payload.limit or 100,
        aliases=keyword.aliases,
        context_hint=keyword.context_hint,
    )

    return {
        "run_id": run.id,
        "keyword_id": keyword.id,
        "keyword": keyword.term,
        "status": run.status,
        "message": "Collection run initiated in background.",
    }


@router.get(
    "/runs/{run_id}",
    response_model=CollectionRunResponse,
)
async def get_run_status(
    run_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionRunResponse:
    """
    Retrieve telemetry, status, per-source counts, and errors for a collection run.
    """
    run = await get_run_by_id(session, run_id=run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "run_not_found", "message": f"Run ID {run_id} not found"},
        )
    return CollectionRunResponse.model_validate(run)
