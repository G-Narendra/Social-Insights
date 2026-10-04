"""
Pydantic schemas for AI summaries, structured insights, trends, comparison, and alerts.
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class InsightItem(BaseModel):
    """An individual structured finding with evidence citations."""

    title: str
    description: str
    evidence_mention_ids: list[int] = Field(default_factory=list)
    volume: int | None = None
    sentiment: str | None = None


class StructuredInsights(BaseModel):
    """Deep AI-synthesized intelligence breakdown."""

    emerging_complaints: list[InsightItem] = Field(default_factory=list)
    requested_features: list[InsightItem] = Field(default_factory=list)
    pain_points: list[InsightItem] = Field(default_factory=list)
    positive_themes: list[InsightItem] = Field(default_factory=list)
    opportunities: list[InsightItem] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    """Response payload for generated AI summary."""

    id: int
    keyword_id: int
    keyword: str
    content: str
    method: str  # llm or template
    model_name: str | None = None
    prompt_version: str | None = None
    created_at: datetime.datetime
    insights: StructuredInsights | None = None


class TrendItem(BaseModel):
    """Metric reflecting rapid topic growth."""

    topic: str
    current_count: int
    previous_count: int
    pct_change: float
    message: str


class TrendsResponse(BaseModel):
    """Trending topics report."""

    keyword: str
    window_days: int
    trends: list[TrendItem]


class CompetitorMetrics(BaseModel):
    """Comparative snapshot for a single keyword/brand."""

    keyword: str
    total_mentions: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    top_topics: list[str]
    common_complaints: list[str]


class CompareResponse(BaseModel):
    """Side-by-side competitor comparison response."""

    competitors: list[CompetitorMetrics]


class AlertResponse(BaseModel):
    """System-generated alert notification."""

    id: int
    keyword_id: int
    keyword: str
    alert_type: str
    severity: str
    message: str
    details: dict[str, Any] | None = None
    created_at: datetime.datetime
    resolved_at: datetime.datetime | None = None

    model_config = {"from_attributes": True}
