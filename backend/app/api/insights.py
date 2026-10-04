"""
API router for AI summaries, structured insights, and trend detection.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import enforce_rate_limit, get_db
from app.ml.summarizer import get_or_generate_summary
from app.ml.trends import detect_trends
from app.schemas.insights import StructuredInsights, SummaryResponse, TrendsResponse
from app.services.keyword_service import get_keyword_by_term

router = APIRouter(prefix="/api", tags=["insights"])


async def _resolve_keyword(session: AsyncSession, keyword: str | None, keyword_id: int | None):
    if keyword_id:
        from app.services.keyword_service import get_keyword_by_id

        kw = await get_keyword_by_id(session, keyword_id)
        if kw:
            return kw
    if keyword:
        kw = await get_keyword_by_term(session, keyword)
        if kw:
            return kw
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "keyword_not_found", "message": "Target keyword not found"},
    )


@router.get("/summary", response_model=SummaryResponse)
@router.get("/insights/summary", response_model=SummaryResponse)
async def get_summary(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
) -> SummaryResponse:
    """
    Retrieve or synthesize an AI executive summary for a keyword.
    Uses fingerprint-based caching.
    """
    kw = await _resolve_keyword(session, keyword, keyword_id)
    return await get_or_generate_summary(session, keyword_id=kw.id, force_refresh=False)


@router.post(
    "/summary/refresh",
    response_model=SummaryResponse,
    dependencies=[Depends(enforce_rate_limit(max_requests=5, window_seconds=60))],
)
async def refresh_summary(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
) -> SummaryResponse:
    """
    Force regeneration of an AI summary (rate-limited).
    """
    kw = await _resolve_keyword(session, keyword, keyword_id)
    return await get_or_generate_summary(session, keyword_id=kw.id, force_refresh=True)


@router.get("/insights", response_model=StructuredInsights)
async def get_insights(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
) -> StructuredInsights:
    """
    Retrieve structured product insights (emerging complaints, requested features, pain points).
    """
    kw = await _resolve_keyword(session, keyword, keyword_id)
    summary_resp = await get_or_generate_summary(session, keyword_id=kw.id, force_refresh=False)
    return summary_resp.insights or StructuredInsights()


@router.get("/trends", response_model=TrendsResponse)
@router.get("/insights/trends", response_model=TrendsResponse)
async def get_topic_trends(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None),
    keyword_id: int | None = Query(default=None),
    window_days: int = Query(default=7, ge=1, le=30),
) -> TrendsResponse:
    """
    Detect rising or declining topics over sliding time windows.
    """
    kw = await _resolve_keyword(session, keyword, keyword_id)
    return await detect_trends(
        session=session,
        keyword_id=kw.id,
        keyword_term=kw.term,
        window_days=window_days,
    )
