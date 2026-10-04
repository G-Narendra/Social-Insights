"""
Pydantic schemas for Collection Runs.
"""

from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectRequest(BaseModel):
    """Payload for triggering a collection run."""

    keyword: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="Brand, product, company or keyword to search for",
    )
    sources: list[str] | None = Field(
        default=None,
        description="List of sources to query (defaults to all enabled sources)",
    )
    limit: int | None = Field(
        default=100,
        ge=10,
        le=500,
        description="Maximum mentions to collect per run",
    )


class CollectionRunResponse(BaseModel):
    """Detailed response for a collection run status."""

    id: int
    keyword_id: int
    keyword: str | None = None
    status: str  # queued, running, partial, succeeded, failed
    started_at: datetime.datetime | None = None
    finished_at: datetime.datetime | None = None
    requested_limit: int | None = None
    per_source: dict[str, Any] | None = None
    errors: list[Any] | None = None

    model_config = {"from_attributes": True}
