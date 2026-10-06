"""
API router for Keyword discovery and tracking.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.db.models import User
from app.schemas.keywords import KeywordCreate, KeywordResponse
from app.services.keyword_service import (
    delete_keyword,
    delete_keyword_by_term,
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
    current_user: Annotated[User, Depends(require_role(["admin", "analyst"]))],
) -> KeywordResponse:
    """
    Add a new keyword or brand to track.
    Requires Admin or Analyst permissions.
    """
    kw = await get_or_create_keyword(
        session,
        term=payload.term,
        aliases=payload.aliases,
        context_hint=payload.context_hint,
    )
    return KeywordResponse.model_validate(kw)


@router.delete("/{keyword_id}", status_code=status.HTTP_200_OK)
async def delete_tracked_keyword_by_id(
    keyword_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
) -> dict[str, Any]:
    """
    Delete a tracked keyword and all its associated mentions, runs, alerts, and summaries.
    Requires Admin permissions.
    """
    success = await delete_keyword(session, keyword_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with ID {keyword_id} not found",
        )
    return {"message": "Keyword successfully deleted", "keyword_id": keyword_id}


@router.delete("", status_code=status.HTTP_200_OK)
async def delete_tracked_keyword_by_query(
    session: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(["admin"]))],
    keyword_id: int | None = Query(default=None),
    term: str | None = Query(default=None),
) -> dict[str, Any]:
    """
    Delete a tracked keyword by query param (keyword_id or term).
    """
    if keyword_id is not None:
        success = await delete_keyword(session, keyword_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Keyword with ID {keyword_id} not found",
            )
        return {"message": "Keyword successfully deleted", "keyword_id": keyword_id}
    elif term is not None:
        success = await delete_keyword_by_term(session, term)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Keyword '{term}' not found",
            )
        return {"message": "Keyword successfully deleted", "term": term}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either keyword_id or term to delete",
        )
