"""
API router for Multi-Brand Competitor Comparison (BON-02).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.ml.compare import compare_keywords
from app.schemas.insights import CompareResponse

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("", response_model=CompareResponse)
async def get_competitor_comparison(
    session: Annotated[AsyncSession, Depends(get_db)],
    keywords: str = Query(
        ...,
        description="Comma-separated list of up to 4 keywords (e.g. 'Toyota,Honda,Tesla')",
    ),
) -> CompareResponse:
    """
    Compare volume, sentiment split, top topics, and common complaints across brands.
    """
    term_list = [k.strip() for k in keywords.split(",") if k.strip()]
    return await compare_keywords(session, term_list)
