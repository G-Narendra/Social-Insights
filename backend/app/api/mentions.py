"""
API router for Mention queries, search, filtering, and pagination.
"""

from __future__ import annotations

import datetime
import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.mentions import (
    MentionFilterParams,
    MentionResponse,
    PaginatedMentionsResponse,
)
from app.services.keyword_service import get_keyword_by_term
from app.services.mention_service import get_mentions

router = APIRouter(prefix="/api/mentions", tags=["mentions"])


@router.get("", response_model=PaginatedMentionsResponse)
async def list_mentions(
    session: Annotated[AsyncSession, Depends(get_db)],
    keyword: str | None = Query(default=None, description="Keyword term to filter by"),
    keyword_id: int | None = Query(default=None, description="Keyword primary key ID"),
    q: str | None = Query(default=None, description="Text search substring"),
    sentiment: str | None = Query(default=None, description="positive, neutral, negative"),
    topic: str | None = Query(default=None, description="Topic name to filter by"),
    source: str | None = Query(default=None, description="hackernews, googlenews, reddit, etc."),
    status: str | None = Query(
        default="done", description="Pipeline status: done, dropped, relevant"
    ),
    date_from: datetime.datetime | None = Query(default=None),
    date_to: datetime.datetime | None = Query(default=None),
    sort: str = Query(default="newest", description="newest, oldest, engagement"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedMentionsResponse:
    """
    Search and filter mentions with server-side pagination.
    """
    target_keyword_id = keyword_id
    if not target_keyword_id and keyword:
        kw = await get_keyword_by_term(session, keyword)
        if kw:
            target_keyword_id = kw.id

    params = MentionFilterParams(
        keyword_id=target_keyword_id,
        q=q,
        sentiment=sentiment,
        topic=topic,
        source=source,
        status=status,
        date_from=date_from,
        date_to=date_to,
        sort=sort,
        page=page,
        page_size=page_size,
    )

    items, total = await get_mentions(session, params)
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return PaginatedMentionsResponse(
        items=[MentionResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
