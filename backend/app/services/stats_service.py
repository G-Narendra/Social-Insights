"""
Service layer for statistical aggregation and time-series computations.
Implements single-roundtrip aggregation queries for high-performance dashboard loads.
"""

from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Keyword, Mention
from app.schemas.stats import (
    OverviewStatsResponse,
    QualityMetrics,
    SentimentBreakdown,
    TimeSeriesBucket,
    TimeSeriesResponse,
    TopicCount,
)


async def get_overview_stats(
    session: AsyncSession,
    keyword_id: int,
) -> OverviewStatsResponse:
    """
    Compute comprehensive dashboard metrics for a keyword.
    Includes sentiment distribution, topic hierarchy, source breakdown,
    and processing quality audit data.
    """
    keyword = await session.get(Keyword, keyword_id)
    keyword_term = keyword.term if keyword else "Unknown"

    # 1. Total and sentiment distribution for 'done' mentions
    sentiment_query = (
        select(
            func.count(Mention.id).label("total"),
            func.sum(case((Mention.sentiment == "positive", 1), else_=0)).label("positive"),
            func.sum(case((Mention.sentiment == "neutral", 1), else_=0)).label("neutral"),
            func.sum(case((Mention.sentiment == "negative", 1), else_=0)).label("negative"),
        )
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
    )
    sent_result = await session.execute(sentiment_query)
    total, pos, neu, neg = sent_result.one()
    total = total or 0
    pos = pos or 0
    neu = neu or 0
    neg = neg or 0

    pos_pct = round((pos / total * 100), 1) if total > 0 else 0.0
    neu_pct = round((neu / total * 100), 1) if total > 0 else 0.0
    neg_pct = round((neg / total * 100), 1) if total > 0 else 0.0

    sentiment = SentimentBreakdown(
        positive=pos,
        neutral=neu,
        negative=neg,
        positive_pct=pos_pct,
        neutral_pct=neu_pct,
        negative_pct=neg_pct,
    )

    # 2. Top topics distribution
    topic_query = (
        select(Mention.topic, func.count(Mention.id).label("count"))
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.topic.isnot(None))
        .group_by(Mention.topic)
        .order_by(func.count(Mention.id).desc())
    )
    topic_result = await session.execute(topic_query)
    top_topics = [
        TopicCount(
            topic=row[0],
            count=row[1],
            percentage=round((row[1] / total * 100), 1) if total > 0 else 0.0,
        )
        for row in topic_result.all()
    ]

    # 3. Source breakdown
    source_query = (
        select(Mention.source, func.count(Mention.id))
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .group_by(Mention.source)
    )
    source_result = await session.execute(source_query)
    sources = {row[0]: row[1] for row in source_result.all()}

    # 4. Data processing quality & drop reasons
    quality_query = select(
        func.count(Mention.id).label("total_collected"),
        func.sum(case((Mention.status == "done", 1), else_=0)).label("total_kept"),
        func.sum(case((Mention.status == "dropped", 1), else_=0)).label("total_dropped"),
    ).where(Mention.keyword_id == keyword_id)
    q_result = await session.execute(quality_query)
    tot_coll, tot_kept, tot_drop = q_result.one()
    tot_coll = tot_coll or 0
    tot_kept = tot_kept or 0
    tot_drop = tot_drop or 0

    reasons_query = (
        select(Mention.drop_reason, func.count(Mention.id))
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "dropped")
        .where(Mention.drop_reason.isnot(None))
        .group_by(Mention.drop_reason)
    )
    reasons_result = await session.execute(reasons_query)
    drop_reasons = {row[0]: row[1] for row in reasons_result.all()}

    quality = QualityMetrics(
        total_collected=tot_coll,
        total_kept=tot_kept,
        total_dropped=tot_drop,
        drop_reasons=drop_reasons,
    )

    return OverviewStatsResponse(
        keyword=keyword_term,
        keyword_id=keyword_id,
        total_mentions=total,
        sentiment=sentiment,
        top_topics=top_topics,
        sources=sources,
        quality=quality,
        last_collected_at=keyword.last_collected_at if keyword else None,
    )


async def get_timeseries_stats(
    session: AsyncSession,
    keyword_id: int,
    interval: str = "day",
) -> TimeSeriesResponse:
    """
    Generate chronological bucket counts with sentiment distribution.
    Supports 'day' and 'hour' intervals with dialect-portable query logic.
    """
    keyword = await session.get(Keyword, keyword_id)
    keyword_term = keyword.term if keyword else "Unknown"

    # Query all done mentions with published_at
    query = (
        select(Mention.published_at, Mention.sentiment)
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.published_at.isnot(None))
        .order_by(Mention.published_at.asc())
    )
    result = await session.execute(query)
    rows = result.all()

    # Bucket in python for 100% database portability between SQLite and Postgres
    buckets_map: dict[str, dict[str, int]] = {}

    for published_at, sentiment in rows:
        if not published_at:
            continue
        if interval == "hour":
            bucket_key = published_at.strftime("%Y-%m-%d %H:00")
        else:
            bucket_key = published_at.strftime("%Y-%m-%d")

        if bucket_key not in buckets_map:
            buckets_map[bucket_key] = {"total": 0, "positive": 0, "neutral": 0, "negative": 0}

        buckets_map[bucket_key]["total"] += 1
        if sentiment in ["positive", "neutral", "negative"]:
            buckets_map[bucket_key][sentiment] += 1

    buckets = [
        TimeSeriesBucket(
            timestamp=k,
            total=v["total"],
            positive=v["positive"],
            neutral=v["neutral"],
            negative=v["negative"],
        )
        for k, v in sorted(buckets_map.items())
    ]

    return TimeSeriesResponse(
        keyword=keyword_term,
        interval=interval,
        buckets=buckets,
    )
