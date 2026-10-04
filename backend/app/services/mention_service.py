"""
Service layer for Mention ingestion, retrieval, filtering, and state transitions.
Ensures database-level idempotency and clean state machine progression.
"""

from __future__ import annotations

import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mention
from app.schemas.mentions import MentionFilterParams, RawMention


async def upsert_mention(
    session: AsyncSession,
    keyword_id: int,
    run_id: int,
    raw: RawMention,
    content_hash: str | None = None,
    canonical_url: str | None = None,
) -> tuple[Mention, bool]:
    """
    Idempotent insert or retrieval of a mention.
    Returns (mention, created) where created is True if newly inserted.
    Guarantees no duplicate (source, source_id) pairs are inserted.
    """
    query = select(Mention).where(
        Mention.source == raw.source,
        Mention.source_id == raw.source_id,
    )
    result = await session.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        return existing, False

    mention = Mention(
        keyword_id=keyword_id,
        run_id=run_id,
        source=raw.source,
        source_id=raw.source_id,
        url=raw.url,
        canonical_url=canonical_url or raw.canonical_url or raw.url,
        title=raw.title,
        text_raw=raw.text,
        text_clean=None,
        content_hash=content_hash,
        author=raw.author,
        published_at=raw.published_at,
        collected_at=datetime.datetime.now(datetime.UTC),
        engagement=raw.engagement or {},
        status="collected",
    )
    session.add(mention)
    await session.commit()
    await session.refresh(mention)
    return mention, True


async def get_mentions(
    session: AsyncSession,
    params: MentionFilterParams,
) -> tuple[list[Mention], int]:
    """
    Query mentions with full filtering, sorting, and pagination.
    Returns (items, total_count).
    """
    query = select(Mention)

    # Filter by keyword_id if specified
    if params.keyword_id:
        query = query.where(Mention.keyword_id == params.keyword_id)

    # Filter by status (default is 'done' for dashboard)
    if params.status:
        query = query.where(Mention.status == params.status)

    # Filter by sentiment
    if params.sentiment:
        query = query.where(Mention.sentiment == params.sentiment)

    # Filter by topic
    if params.topic:
        query = query.where(
            or_(
                Mention.topic == params.topic,
                Mention.secondary_topic == params.topic,
            )
        )

    # Filter by source
    if params.source:
        query = query.where(Mention.source == params.source)

    # Date range filters
    if params.date_from:
        query = query.where(Mention.published_at >= params.date_from)
    if params.date_to:
        query = query.where(Mention.published_at <= params.date_to)

    # Full text / keyword search
    if params.q:
        search_term = f"%{params.q.strip().lower()}%"
        query = query.where(
            or_(
                func.lower(Mention.text_raw).like(search_term),
                func.lower(Mention.title).like(search_term),
            )
        )

    # Count total matching rows
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Apply sorting
    if params.sort == "oldest":
        query = query.order_by(Mention.published_at.asc().nulls_last(), Mention.id.asc())
    elif params.sort == "engagement":
        # Sort by engagement score if available in json
        query = query.order_by(Mention.published_at.desc().nulls_last())
    else:  # "newest"
        query = query.order_by(Mention.published_at.desc().nulls_last(), Mention.id.desc())

    # Pagination
    offset = (params.page - 1) * params.page_size
    query = query.limit(params.page_size).offset(offset)

    result = await session.execute(query)
    items = list(result.scalars().all())

    return items, total


async def update_mention_status(
    session: AsyncSession,
    mention_id: int,
    status: str,
    drop_reason: str | None = None,
) -> None:
    """Transition mention status in the processing state machine."""
    mention = await session.get(Mention, mention_id)
    if mention:
        mention.status = status
        if drop_reason:
            mention.drop_reason = drop_reason
        await session.commit()


async def update_mention_enrichment(
    session: AsyncSession,
    mention_id: int,
    sentiment: str,
    sentiment_score: float,
    topic: str,
    topic_score: float,
    secondary_topic: str | None = None,
    enriched_by: str = "model",
    embedding: list[float] | None = None,
) -> None:
    """Save NLP enrichment predictions to the mention."""
    mention = await session.get(Mention, mention_id)
    if mention:
        mention.sentiment = sentiment
        mention.sentiment_score = sentiment_score
        mention.topic = topic
        mention.topic_score = topic_score
        mention.secondary_topic = secondary_topic
        mention.enriched_by = enriched_by
        if embedding:
            mention.embedding = embedding
        mention.status = "done"
        await session.commit()
