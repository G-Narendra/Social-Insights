"""Initial schema: keywords, collection_runs, mentions, summaries, alerts

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-10-05 01:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. keywords table
    op.create_table(
        "keywords",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("term", sa.String(length=80), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=True),
        sa.Column("context_hint", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_collected_at", sa.DateTime(), nullable=True),
        sa.Column("is_tracked", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_keywords_term", "keywords", ["term"], unique=True)

    # 2. collection_runs table
    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("requested_limit", sa.Integer(), nullable=True),
        sa.Column("per_source", sa.JSON(), nullable=True),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_collection_runs_keyword_id", "collection_runs", ["keyword_id"])

    # 3. mentions table
    op.create_table(
        "mentions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("text_raw", sa.Text(), nullable=False),
        sa.Column("text_clean", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("collected_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("engagement", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="collected"),
        sa.Column("drop_reason", sa.String(length=50), nullable=True),
        sa.Column("sentiment", sa.String(length=10), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("topic", sa.String(length=30), nullable=True),
        sa.Column("topic_score", sa.Float(), nullable=True),
        sa.Column("secondary_topic", sa.String(length=30), nullable=True),
        sa.Column("enriched_by", sa.String(length=10), nullable=True),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_id", name="uq_source_source_id"),
    )
    op.create_index("ix_mentions_keyword_id", "mentions", ["keyword_id"])
    op.create_index("ix_mentions_run_id", "mentions", ["run_id"])
    op.create_index("ix_mentions_source", "mentions", ["source"])
    op.create_index("ix_mentions_content_hash", "mentions", ["content_hash"])
    op.create_index("ix_mentions_canonical_url", "mentions", ["canonical_url"])
    op.create_index("ix_mention_keyword_published", "mentions", ["keyword_id", "published_at"])
    op.create_index("ix_mention_keyword_sentiment", "mentions", ["keyword_id", "sentiment"])
    op.create_index("ix_mention_keyword_topic", "mentions", ["keyword_id", "topic"])

    # 4. summaries table
    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("data_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("prompt_version", sa.String(length=20), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("insights", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_summaries_keyword_id", "summaries", ["keyword_id"])

    # 5. alerts table
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keyword_id", sa.Integer(), nullable=False),
        sa.Column("alert_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=10), nullable=False, server_default="warning"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_keyword_id", "alerts", ["keyword_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("summaries")
    op.drop_table("mentions")
    op.drop_table("collection_runs")
    op.drop_table("keywords")
