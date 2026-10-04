"""
Service layer for Keyword operations.
Provides CRUD and metadata management for tracked brand/search terms.
"""

from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Keyword, Mention


async def get_or_create_keyword(
    session: AsyncSession,
    term: str,
    aliases: list[str] | None = None,
    context_hint: str | None = None,
) -> Keyword:
    """Retrieve an existing keyword or create a new one."""
    normalized_term = term.strip()
    query = select(Keyword).where(func.lower(Keyword.term) == func.lower(normalized_term))
    result = await session.execute(query)
    keyword = result.scalar_one_or_none()

    if keyword is None:
        keyword = Keyword(
            term=normalized_term,
            aliases=aliases or [],
            context_hint=context_hint,
            is_tracked=True,
        )
        session.add(keyword)
        await session.commit()
        await session.refresh(keyword)

    return keyword


async def get_keyword_by_id(session: AsyncSession, keyword_id: int) -> Keyword | None:
    """Find a keyword by its primary key ID."""
    return await session.get(Keyword, keyword_id)


async def get_keyword_by_term(session: AsyncSession, term: str) -> Keyword | None:
    """Find a keyword by its term string (case-insensitive)."""
    normalized = term.strip()
    query = select(Keyword).where(func.lower(Keyword.term) == func.lower(normalized))
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def list_keywords(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    List all tracked keywords with mention counts.
    Single round-trip aggregated query using LEFT OUTER JOIN.
    """
    query = (
        select(
            Keyword,
            func.count(Mention.id).label("mention_count"),
        )
        .outerjoin(Mention, Keyword.id == Mention.keyword_id)
        .group_by(Keyword.id)
        .order_by(Keyword.last_collected_at.desc().nulls_last(), Keyword.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(query)
    rows = result.all()

    items = []
    for kw, count in rows:
        items.append(
            {
                "id": kw.id,
                "term": kw.term,
                "aliases": kw.aliases or [],
                "context_hint": kw.context_hint,
                "created_at": kw.created_at,
                "last_collected_at": kw.last_collected_at,
                "is_tracked": kw.is_tracked,
                "mention_count": count,
            }
        )
    return items


async def update_last_collected(
    session: AsyncSession,
    keyword_id: int,
    timestamp: datetime.datetime | None = None,
) -> None:
    """Update last collection timestamp for a keyword."""
    keyword = await session.get(Keyword, keyword_id)
    if keyword:
        keyword.last_collected_at = timestamp or datetime.datetime.now(datetime.UTC)
        await session.commit()
