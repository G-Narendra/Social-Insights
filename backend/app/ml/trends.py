"""
Trend Detection Engine (BON-01).
Analyzes topic velocity over sliding time windows (current vs previous N days).
Computes percentage changes and formats natural language trend insights.
"""

from __future__ import annotations

import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mention
from app.schemas.insights import TrendItem, TrendsResponse


async def detect_trends(
    session: AsyncSession,
    keyword_id: int,
    keyword_term: str,
    window_days: int = 7,
    min_volume: int = 5,
) -> TrendsResponse:
    """
    Compare topic volume in the current window vs the prior window:
    - Current window: [now - N days, now]
    - Previous window: [now - 2N days, now - N days]
    Computes percentage change: (current - previous) / max(previous, 1) * 100
    Ranks top rising topics exceeding min_volume.
    """
    now = datetime.datetime.now(datetime.UTC)
    current_start = now - datetime.timedelta(days=window_days)
    previous_start = now - datetime.timedelta(days=2 * window_days)

    # 1. Topic counts in current window
    curr_query = (
        select(Mention.topic, func.count(Mention.id).label("count"))
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.published_at >= current_start)
        .where(Mention.published_at <= now)
        .where(Mention.topic.isnot(None))
        .group_by(Mention.topic)
    )
    curr_rows = (await session.execute(curr_query)).all()
    curr_counts = {row[0]: row[1] for row in curr_rows}

    # 2. Topic counts in previous window
    prev_query = (
        select(Mention.topic, func.count(Mention.id).label("count"))
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.published_at >= previous_start)
        .where(Mention.published_at < current_start)
        .where(Mention.topic.isnot(None))
        .group_by(Mention.topic)
    )
    prev_rows = (await session.execute(prev_query)).all()
    prev_counts = {row[0]: row[1] for row in prev_rows}

    trend_items: list[TrendItem] = []

    all_topics = set(curr_counts.keys()) | set(prev_counts.keys())

    for topic in all_topics:
        c = curr_counts.get(topic, 0)
        p = prev_counts.get(topic, 0)

        # Enforce minimum volume threshold to avoid tiny-number percentage noise
        if c < min_volume and p < min_volume:
            continue

        pct_change = round(((c - p) / max(p, 1)) * 100, 1)
        direction = "increased" if pct_change >= 0 else "decreased"

        message = (
            f"{topic.replace('_', ' ').title()} mentions {direction} {abs(pct_change):.0f}% "
            f"over the last {window_days} days ({p} to {c})."
        )

        trend_items.append(
            TrendItem(
                topic=topic,
                current_count=c,
                previous_count=p,
                pct_change=pct_change,
                message=message,
            )
        )

    # Sort by highest growth percentage
    trend_items.sort(key=lambda t: t.pct_change, reverse=True)

    return TrendsResponse(
        keyword=keyword_term,
        window_days=window_days,
        trends=trend_items[:5],
    )
