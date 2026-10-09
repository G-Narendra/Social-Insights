"""
SQLAlchemy ORM models for the social listening platform.

Schema design rationale (documented in ARCHITECTURE.md):
- Separate raw and cleaned text for auditability.
- Status field on mentions enables a resumable pipeline state machine.
- Dropped mentions are kept (not deleted) with a drop_reason for debugging.
- Unique constraints on (source, source_id) enforce dedup at the DB level.
- Indexes on (keyword_id, published_at) and (keyword_id, sentiment) support
  efficient dashboard aggregate queries.
"""

from __future__ import annotations

import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class UTCDateTime(TypeDecorator):
    """
    Ensures datetime objects are converted to naive UTC for storage
    in PostgreSQL 'timestamp without time zone' (and SQLite) without asyncpg
    type errors, and returned as timezone-aware UTC datetimes on load.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and isinstance(value, datetime.datetime):
            if value.tzinfo is not None:
                return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return value
        return value

    def process_result_value(self, value, dialect):
        if value is not None and isinstance(value, datetime.datetime) and value.tzinfo is None:
            return value.replace(tzinfo=datetime.timezone.utc)
        return value


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Keyword(Base):
    """A tracked search term with optional aliases and disambiguation context."""

    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    term: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    aliases: Mapped[dict | None] = mapped_column(JSON, default=list)
    context_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )
    last_collected_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CollectionRun(Base):
    """Records a single data collection run for a keyword."""

    __tablename__ = "collection_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued"
    )  # queued, running, partial, succeeded, failed
    started_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    finished_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    requested_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_source: Mapped[dict | None] = mapped_column(JSON, default=dict)
    errors: Mapped[dict | None] = mapped_column(JSON, default=list)


class Mention(Base):
    """A single public mention of a keyword from any source."""

    __tablename__ = "mentions"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_source_source_id"),
        Index("ix_mention_keyword_published", "keyword_id", "published_at"),
        Index("ix_mention_keyword_sentiment", "keyword_id", "sentiment"),
        Index("ix_mention_keyword_topic", "keyword_id", "topic"),
        Index("ix_mention_content_hash", "content_hash"),
        Index("ix_mention_canonical_url", "canonical_url"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_raw: Mapped[str] = mapped_column(Text, nullable=False)
    text_clean: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)
    collected_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    engagement: Mapped[dict | None] = mapped_column(JSON, default=dict)

    # Pipeline state machine
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="collected"
    )  # collected, normalized, deduped, relevant, enriched, done, dropped
    drop_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # AI enrichment results
    sentiment: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(30), nullable=True)
    topic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    secondary_topic: Mapped[str | None] = mapped_column(String(30), nullable=True)
    enriched_by: Mapped[str | None] = mapped_column(String(10), nullable=True)  # rules, model, llm

    # Embedding stored as JSON array (avoids pgvector dependency for portability)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)


class Summary(Base):
    """AI-generated summary of mentions for a keyword."""

    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    data_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # llm or template
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    insights: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )


class Alert(Base):
    """System-generated alert for significant changes in mention patterns."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    keyword_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="warning")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(UTCDateTime, nullable=True)


class User(Base):
    """User account with role-based access control (admin, analyst, viewer)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), default="analyst", nullable=False
    )  # admin, analyst, viewer
    full_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), nullable=False
    )
