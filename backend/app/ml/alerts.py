"""
Anomaly & Sentiment Spike Alert Engine (BON-04).
Monitors rolling 14-day baseline of negative sentiment volume.
Triggers persistent alert records when negative sentiment exceeds mean + k * std.
"""

from __future__ import annotations

import datetime
import math
from typing import Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, Mention
from app.schemas.insights import AlertResponse


async def evaluate_sentiment_spike_alerts(
    session: AsyncSession,
    keyword_id: int,
    keyword_term: str,
    baseline_days: int = 14,
    k_std_threshold: float = 2.0,
    min_today_volume: int = 5,
) -> Alert | None:
    """
    Evaluate if today's negative sentiment ratio constitutes a statistically significant spike.
    Baseline = mean + k * std of daily negative share over previous 14 days.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
    baseline_start = today_start - datetime.timedelta(days=baseline_days)

    # 1. Fetch today's volume & negative count
    today_query = (
        select(
            func.count(Mention.id).label("total"),
            func.sum(func.case((Mention.sentiment == "negative", 1), else_=0)).label("neg"),
        )
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.published_at >= today_start)
    )
    today_total, today_neg = (await session.execute(today_query)).one()
    today_total = today_total or 0
    today_neg = today_neg or 0

    if today_total < min_today_volume:
        return None  # Volume too small for statistical significance

    today_share = today_neg / today_total

    # 2. Compute historical daily negative share for each day in baseline window
    hist_query = (
        select(Mention.published_at, Mention.sentiment)
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .where(Mention.published_at >= baseline_start)
        .where(Mention.published_at < today_start)
    )
    hist_rows = (await session.execute(hist_query)).all()

    daily_totals: dict[str, int] = {}
    daily_negs: dict[str, int] = {}

    for pub, sent in hist_rows:
        if not pub:
            continue
        day_str = pub.strftime("%Y-%m-%d")
        daily_totals[day_str] = daily_totals.get(day_str, 0) + 1
        if sent == "negative":
            daily_negs[day_str] = daily_negs.get(day_str, 0) + 1

    # Calculate daily negative proportions
    daily_shares: list[float] = []
    for day, tot in daily_totals.items():
        if tot >= 3:  # Only days with representative volume
            daily_shares.append(daily_negs.get(day, 0) / tot)

    # If insufficient history, use standard threshold (e.g. 40% negative with min volume)
    if len(daily_shares) < 3:
        if today_share >= 0.45:
            return await _create_or_get_alert(
                session=session,
                keyword_id=keyword_id,
                keyword=keyword_term,
                severity="critical" if today_share >= 0.60 else "warning",
                message=f"Elevated negative sentiment detected: {today_share:.1%} of mentions today are negative.",
                details={"today_share": today_share, "today_volume": today_total},
            )
        return None

    # Calculate mean and standard deviation
    mean = sum(daily_shares) / len(daily_shares)
    variance = sum((x - mean) ** 2 for x in daily_shares) / len(daily_shares)
    std = math.sqrt(variance)
    threshold = mean + (k_std_threshold * max(std, 0.05))

    if today_share > threshold:
        msg = (
            f"Negative sentiment spike detected: {today_share:.1%} negative today vs "
            f"{mean:.1%} 14-day rolling baseline (+{((today_share - mean) / max(mean, 0.01)) * 100:.0f}% spike)."
        )
        return await _create_or_get_alert(
            session=session,
            keyword_id=keyword_id,
            keyword=keyword_term,
            severity="critical" if today_share >= 0.50 else "warning",
            message=msg,
            details={
                "today_share": round(today_share, 3),
                "baseline_mean": round(mean, 3),
                "baseline_std": round(std, 3),
                "threshold": round(threshold, 3),
                "volume": today_total,
            },
        )

    return None


async def _create_or_get_alert(
    session: AsyncSession,
    keyword_id: int,
    keyword: str,
    severity: str,
    message: str,
    details: dict,
) -> Alert:
    """Check for existing unresolved alert in last 24h to avoid alert fatigue."""
    twenty_four_hours_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=24)
    existing_query = (
        select(Alert)
        .where(Alert.keyword_id == keyword_id)
        .where(Alert.alert_type == "sentiment_spike")
        .where(Alert.resolved_at.is_(None))
        .where(Alert.created_at >= twenty_four_hours_ago)
        .limit(1)
    )
    existing = (await session.execute(existing_query)).scalar_one_or_none()
    if existing:
        return existing

    new_alert = Alert(
        keyword_id=keyword_id,
        alert_type="sentiment_spike",
        severity=severity,
        message=message,
        details=details,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    session.add(new_alert)
    await session.commit()
    await session.refresh(new_alert)
    return new_alert


async def list_active_alerts(
    session: AsyncSession,
    keyword_id: int | None = None,
) -> list[Alert]:
    """Retrieve all unresolved active alerts."""
    query = select(Alert).where(Alert.resolved_at.is_(None)).order_by(Alert.created_at.desc())
    if keyword_id:
        query = query.where(Alert.keyword_id == keyword_id)
    result = await session.execute(query)
    return list(result.scalars().all())
