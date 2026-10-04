"""
API router for Keyword discovery and tracking.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.keywords import KeywordCreate, KeywordResponse
from app.services.keyword_service import (
    get_or_create_keyword,
    list_keywords,
)

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[dict[str, Any]])
async def get_tracked_keywords(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """
    List all tracked keywords with mention counts and last collection timestamps.
    """
    return await list_keywords(session, limit=limit, offset=offset)


@router.post("", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword(
    payload: KeywordCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> KeywordResponse:
    """
    Add a new keyword or brand to track.
    """
    kw = await get_or_create_keyword(
        session,
        term=payload.term,
        aliases=payload.aliases,
        context_hint=payload.context_hint,
    )
    return KeywordResponse.model_validate(kw)
