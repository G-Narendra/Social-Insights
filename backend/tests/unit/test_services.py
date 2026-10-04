"""
Unit tests for Keyword, Mention, Run, and Stats services.
Validates constraints, upsert idempotency, and aggregate calculations on in-memory SQLite.
"""

from __future__ import annotations

import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mentions import MentionFilterParams, RawMention
from app.services.keyword_service import (
    get_keyword_by_id,
    get_keyword_by_term,
    get_or_create_keyword,
    list_keywords,
)
from app.services.mention_service import (
    get_mentions,
    update_mention_enrichment,
    update_mention_status,
    upsert_mention,
)
from app.services.stats_service import get_overview_stats, get_timeseries_stats


class TestKeywordService:
    @pytest.mark.asyncio
    async def test_get_or_create_and_retrieve(self, db_session: AsyncSession) -> None:
        kw1 = await get_or_create_keyword(db_session, "Toyota", aliases=["TM"])
        assert kw1.id is not None
        assert kw1.term == "Toyota"
        assert kw1.aliases == ["TM"]

        # Re-requesting with different case returns the exact same record
        kw2 = await get_or_create_keyword(db_session, "toyota")
        assert kw2.id == kw1.id

        by_id = await get_keyword_by_id(db_session, kw1.id)
        assert by_id is not None
        assert by_id.id == kw1.id

        by_term = await get_keyword_by_term(db_session, "TOYOTA")
        assert by_term is not None
        assert by_term.id == kw1.id

    @pytest.mark.asyncio
    async def test_list_keywords_with_counts(self, db_session: AsyncSession) -> None:
        kw = await get_or_create_keyword(db_session, "Tesla")
        raw = RawMention(
            source="hackernews",
            source_id="item-100",
            text="Tesla Model 3 review",
            keyword="Tesla",
        )
        await upsert_mention(db_session, kw.id, run_id=1, raw=raw)

        kw_list = await list_keywords(db_session)
        assert len(kw_list) >= 1
        tesla_entry = next(k for k in kw_list if k["term"] == "Tesla")
        assert tesla_entry["mention_count"] == 1


class TestMentionService:
    @pytest.mark.asyncio
    async def test_upsert_idempotency(self, db_session: AsyncSession) -> None:
        """Inserting identical (source, source_id) twice must return existing and leave 1 row."""
        kw = await get_or_create_keyword(db_session, "Apple")
        raw = RawMention(
            source="reddit",
            source_id="post_999",
            text="Apple announces M4 chips",
            title="M4 Announcement",
            keyword="Apple",
        )

        mention1, created1 = await upsert_mention(db_session, kw.id, run_id=1, raw=raw)
        assert created1 is True
        assert mention1.source_id == "post_999"

        mention2, created2 = await upsert_mention(db_session, kw.id, run_id=1, raw=raw)
        assert created2 is False
        assert mention2.id == mention1.id

    @pytest.mark.asyncio
    async def test_filter_and_search_mentions(self, db_session: AsyncSession) -> None:
        kw = await get_or_create_keyword(db_session, "Google")
        raw1 = RawMention(
            source="hackernews",
            source_id="hn_1",
            text="Google Cloud outage in us-east",
            title="GCP Incident",
            keyword="Google",
            published_at=datetime.datetime(2026, 1, 15, 10, 0),
        )
        raw2 = RawMention(
            source="reddit",
            source_id="rd_2",
            text="Pixel 9 camera is incredible",
            title="Pixel Review",
            keyword="Google",
            published_at=datetime.datetime(2026, 1, 16, 12, 0),
        )

        m1, _ = await upsert_mention(db_session, kw.id, run_id=1, raw=raw1)
        m2, _ = await upsert_mention(db_session, kw.id, run_id=1, raw=raw2)

        # Enrich and set status to 'done'
        await update_mention_enrichment(
            db_session,
            m1.id,
            sentiment="negative",
            sentiment_score=0.92,
            topic="quality",
            topic_score=0.88,
        )
        await update_mention_enrichment(
            db_session,
            m2.id,
            sentiment="positive",
            sentiment_score=0.95,
            topic="product",
            topic_score=0.91,
        )

        # 1. Filter by sentiment
        params = MentionFilterParams(keyword_id=kw.id, sentiment="negative")
        items, total = await get_mentions(db_session, params)
        assert total == 1
        assert items[0].id == m1.id

        # 2. Text search with 'q'
        params_q = MentionFilterParams(keyword_id=kw.id, q="Pixel")
        items_q, total_q = await get_mentions(db_session, params_q)
        assert total_q == 1
        assert items_q[0].id == m2.id


class TestStatsService:
    @pytest.mark.asyncio
    async def test_overview_and_timeseries_aggregates(self, db_session: AsyncSession) -> None:
        """Validate exact hand-computed aggregations."""
        kw = await get_or_create_keyword(db_session, "Toyota")

        # Create 5 positive, 3 neutral, 2 negative mentions
        specs = [
            ("s1", "positive", "quality", "hackernews", datetime.datetime(2026, 1, 10, 8, 0)),
            ("s2", "positive", "quality", "hackernews", datetime.datetime(2026, 1, 10, 9, 0)),
            ("s3", "positive", "product", "reddit", datetime.datetime(2026, 1, 10, 10, 0)),
            ("s4", "positive", "features", "reddit", datetime.datetime(2026, 1, 11, 12, 0)),
            ("s5", "positive", "features", "googlenews", datetime.datetime(2026, 1, 11, 14, 0)),
            ("s6", "neutral", "product", "googlenews", datetime.datetime(2026, 1, 10, 15, 0)),
            ("s7", "neutral", "other", "reddit", datetime.datetime(2026, 1, 11, 16, 0)),
            ("s8", "neutral", "other", "hackernews", datetime.datetime(2026, 1, 11, 17, 0)),
            ("s9", "negative", "pricing", "reddit", datetime.datetime(2026, 1, 10, 18, 0)),
            ("s10", "negative", "complaints", "reddit", datetime.datetime(2026, 1, 11, 19, 0)),
        ]

        for idx, (_sid, sent, top, src, pub) in enumerate(specs):
            raw = RawMention(
                source=src,
                source_id=f"test_{idx}",
                text=f"Toyota review {idx}",
                keyword="Toyota",
                published_at=pub,
            )
            m, _ = await upsert_mention(db_session, kw.id, run_id=1, raw=raw)
            await update_mention_enrichment(
                db_session,
                m.id,
                sentiment=sent,
                sentiment_score=0.9,
                topic=top,
                topic_score=0.85,
            )

        # Also add 1 dropped mention for data quality stats
        raw_drop = RawMention(
            source="reddit",
            source_id="drop_1",
            text="Irrelevant spam link",
            keyword="Toyota",
        )
        m_drop, _ = await upsert_mention(db_session, kw.id, run_id=1, raw=raw_drop)
        await update_mention_status(
            db_session, m_drop.id, status="dropped", drop_reason="spam_link_density"
        )

        overview = await get_overview_stats(db_session, kw.id)
        assert overview.total_mentions == 10
        assert overview.sentiment.positive == 5
        assert overview.sentiment.neutral == 3
        assert overview.sentiment.negative == 2
        assert overview.sentiment.positive_pct == 50.0
        assert overview.sentiment.neutral_pct == 30.0
        assert overview.sentiment.negative_pct == 20.0

        # Sources: hackernews=3, reddit=5, googlenews=2
        assert overview.sources["hackernews"] == 3
        assert overview.sources["reddit"] == 5
        assert overview.sources["googlenews"] == 2

        # Data quality
        assert overview.quality.total_collected == 11
        assert overview.quality.total_kept == 10
        assert overview.quality.total_dropped == 1
        assert overview.quality.drop_reasons.get("spam_link_density") == 1

        # Time series by day
        ts = await get_timeseries_stats(db_session, kw.id, interval="day")
        assert len(ts.buckets) == 2
        day_1 = next(b for b in ts.buckets if b.timestamp == "2026-01-10")
        day_2 = next(b for b in ts.buckets if b.timestamp == "2026-01-11")
        assert day_1.total == 5
        assert day_2.total == 5
