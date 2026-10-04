"""
API router for statistical aggregates and time-series representations.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.stats import OverviewStatsResponse, TimeSeriesResponse
from app.services.keyword_service import get_keyword_by_term
from app.services.stats_service import get_overview_stats, get_timeseries_stats

router = APIRouter(prefix="/api/stats", tags=["stats"])


async def _resolve_keyword_id(
    session: AsyncSession,
    keyword: str | None,
    keyword_id: int | None,
) -> int:
    """Helper to resolve keyword string or ID to a valid keyword_id."""
    if keyword_id:
        return keyword_id
    if keyword:
        kw = await get_keyword_by_term(session, keyword)
        if kw:
            return kw.id
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "keyword_not_found", "message": "Target keyword not found"},
    )


@router.get("/overview", response_model=OverviewStatsResponse)
async def get_overview(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
) -> OverviewStatsResponse:
    """
    Retrieve executive dashboard overview statistics for a keyword.
    """
    resolved_id = await _resolve_keyword_id(session, keyword, keyword_id)
    return await get_overview_stats(session, resolved_id)


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def get_timeseries(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
    interval: str = Query(default="day", pattern="^(day|hour)$"),
) -> TimeSeriesResponse:
    """
    Retrieve chronological mention frequency and sentiment distribution.
    """
    resolved_id = await _resolve_keyword_id(session, keyword, keyword_id)
    return await get_timeseries_stats(session, resolved_id, interval=interval)
