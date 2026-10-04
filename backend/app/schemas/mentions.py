"""
Pydantic schemas for Mention queries, responses, and raw ingestion data.
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawMention(BaseModel):
    """
    Standard normalized payload emitted by all source connectors.
    Every connector produces items matching this shape.
    """

    source: str = Field(..., description="Unique connector name: hackernews, googlenews, etc.")
    source_id: str = Field(..., description="Unique ID within the source platform")
    url: str | None = Field(default=None, description="Direct URL to mention")
    canonical_url: str | None = Field(default=None, description="Cleaned URL without tracking tags")
    title: str | None = Field(default=None, description="Post/article title if applicable")
    text: str = Field(..., description="Raw text content of the mention")
    author: str | None = Field(default=None, description="Public handle or author name")
    published_at: datetime.datetime | None = Field(
        default=None, description="Publication timestamp"
    )
    engagement: dict[str, Any] = Field(
        default_factory=dict,
        description="Source-specific engagement metrics (score, comments, likes, views)",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Auxiliary metadata (subreddit, publisher, tags)",
    )
    keyword: str = Field(..., description="Target keyword this mention was retrieved for")


class MentionResponse(BaseModel):
    """Schema for individual mentions returned in API queries."""

    id: int
    keyword_id: int
    run_id: int
    source: str
    source_id: str
    url: str | None = None
    canonical_url: str | None = None
    title: str | None = None
    text_raw: str
    text_clean: str | None = None
    author: str | None = None
    published_at: datetime.datetime | None = None
    collected_at: datetime.datetime
    language: str | None = None
    engagement: dict[str, Any] | None = None
    status: str
    drop_reason: str | None = None
    sentiment: str | None = None
    sentiment_score: float | None = None
    topic: str | None = None
    topic_score: float | None = None
    secondary_topic: str | None = None
    enriched_by: str | None = None

    model_config = {"from_attributes": True}


class MentionFilterParams(BaseModel):
    """Query parameter schema for searching and filtering mentions."""

    keyword: str | None = None
    keyword_id: int | None = None
    q: str | None = None
    sentiment: str | None = None
    topic: str | None = None
    source: str | None = None
    status: str | None = "done"  # default to done (ready for dashboard)
    date_from: datetime.datetime | None = None
    date_to: datetime.datetime | None = None
    sort: str = "newest"  # newest, oldest, engagement
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedMentionsResponse(BaseModel):
    """Paginated collection of mentions with metadata."""

    items: list[MentionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
