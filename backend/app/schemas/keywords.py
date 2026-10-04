"""
Pydantic schemas for Keyword management and validation.
"""

from __future__ import annotations

import datetime
import re

from pydantic import BaseModel, Field, field_validator


class KeywordBase(BaseModel):
    """Base schema for keyword validation."""

    term: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="The brand, company, product or keyword to track",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternative names or spellings (e.g. ['Toyota Motor', 'TM'])",
    )
    context_hint: str | None = Field(
        default=None,
        description="Disambiguation hint for ambiguous terms (e.g. 'automotive manufacturer')",
    )

    @field_validator("term")
    @classmethod
    def validate_term(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Keyword term must be at least 2 characters")
        if len(cleaned) > 80:
            raise ValueError("Keyword term must not exceed 80 characters")
        # Disallow dangerous control characters
        if re.search(r"[\x00-\x1f\x7f]", cleaned):
            raise ValueError("Keyword term contains invalid control characters")
        return cleaned


class KeywordCreate(KeywordBase):
    """Schema for creating a new keyword."""

    is_tracked: bool = Field(default=True)


class KeywordResponse(KeywordBase):
    """Schema for keyword API responses."""

    id: int
    created_at: datetime.datetime
    last_collected_at: datetime.datetime | None = None
    is_tracked: bool
    mention_count: int = 0

    model_config = {"from_attributes": True}
