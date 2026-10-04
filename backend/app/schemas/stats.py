"""
Pydantic schemas for statistical summaries and time-series representations.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel


class SentimentBreakdown(BaseModel):
    """Counts and percentages for sentiment distribution."""

    positive: int = 0
    neutral: int = 0
    negative: int = 0
    positive_pct: float = 0.0
    neutral_pct: float = 0.0
    negative_pct: float = 0.0


class TopicCount(BaseModel):
    """Occurrence metrics for a topic."""

    topic: str
    count: int
    percentage: float


class QualityMetrics(BaseModel):
    """Audit metrics on data processing and dropped items."""

    total_collected: int = 0
    total_kept: int = 0
    total_dropped: int = 0
    drop_reasons: dict[str, int] = {}


class OverviewStatsResponse(BaseModel):
    """Executive dashboard summary statistics."""

    keyword: str
    keyword_id: int
    total_mentions: int
    sentiment: SentimentBreakdown
    top_topics: list[TopicCount]
    sources: dict[str, int]
    quality: QualityMetrics
    last_collected_at: datetime.datetime | None = None


class TimeSeriesBucket(BaseModel):
    """Single time interval point for mentions over time."""

    timestamp: str  # ISO string or date representation
    total: int
    positive: int
    neutral: int
    negative: int


class TimeSeriesResponse(BaseModel):
    """Chronological mention distributions over time."""

    keyword: str
    interval: str  # 'day' or 'hour'
    buckets: list[TimeSeriesBucket]
