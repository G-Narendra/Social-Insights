"""
Tests for bonus features (BON-01, BON-02, BON-04).
Validates:
1. Topic acceleration / trend detection with synthetic time-series spike
2. Statistical sentiment spike anomaly alert engine (> baseline mean + 2*std)
3. Multi-brand competitor comparison aggregation
"""

from __future__ import annotations

import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mention
from app.ml.alerts import evaluate_sentiment_spike_alerts
from app.ml.compare import compare_keywords
from app.ml.trends import detect_trends
from app.services.keyword_service import get_or_create_keyword
from app.services.run_service import create_collection_run


class TestBonusFeatures:
    async def test_trending_topics_spike_detection(self, db_session: AsyncSession) -> None:
        """BON-01: Verify detection of a rapid topic spike between sliding windows."""
        kw = await get_or_create_keyword(db_session, "SpikeCorp")
        run = await create_collection_run(db_session, kw.id)
        now = datetime.datetime.now(datetime.UTC)

        # Baseline window (8-14 days ago): only 2 mentions of pricing_billing
        for i in range(2):
            past_date = now - datetime.timedelta(days=10, hours=i)
            mention = Mention(
                keyword_id=kw.id,
                run_id=run.id,
                source="hackernews",
                source_id=f"past_spike_{i}",
                text_raw="Past pricing mention",
                published_at=past_date,
                topic="pricing_billing",
                status="done",
            )
            db_session.add(mention)

        # Current window (last 7 days): 15 mentions of pricing_billing (massive acceleration)
        for i in range(15):
            recent_date = now - datetime.timedelta(days=2, hours=i)
            mention = Mention(
                keyword_id=kw.id,
                run_id=run.id,
                source="hackernews",
                source_id=f"recent_spike_{i}",
                text_raw="Recent high price inflation",
                published_at=recent_date,
                topic="pricing_billing",
                status="done",
            )
            db_session.add(mention)

        await db_session.commit()

        # Run trend detector
        report = await detect_trends(
            session=db_session,
            keyword_id=kw.id,
            keyword_term="SpikeCorp",
            window_days=7,
            min_volume=3,
        )

        assert report.keyword == "SpikeCorp"
        assert len(report.trends) >= 1
        pricing_trend = next((t for t in report.trends if t.topic == "pricing_billing"), None)
        assert pricing_trend is not None
        assert pricing_trend.current_count == 15
        assert pricing_trend.previous_count == 2
        assert pricing_trend.pct_change > 100.0  # 650% increase!
        assert "increased" in pricing_trend.message or "surged" in pricing_trend.message

    async def test_sentiment_spike_alert_trigger(self, db_session: AsyncSession) -> None:
        """BON-04: Verify statistical anomaly trigger on negative sentiment spike."""
        kw = await get_or_create_keyword(db_session, "AlertBrand")
        run = await create_collection_run(db_session, kw.id)
        now = datetime.datetime.now(datetime.UTC)
        today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.UTC)

        # 14-day historical baseline: each day has 10 mentions, 1 negative (10% negative share, low variance)
        for day in range(1, 14):
            day_time = today_start - datetime.timedelta(days=day, hours=12)
            # 9 positive/neutral
            for idx in range(9):
                db_session.add(
                    Mention(
                        keyword_id=kw.id,
                        run_id=run.id,
                        source="hackernews",
                        source_id=f"base_pos_{day}_{idx}",
                        text_raw="Good steady performance",
                        published_at=day_time,
                        sentiment="positive",
                        status="done",
                    )
                )
            # 1 negative
            db_session.add(
                Mention(
                    keyword_id=kw.id,
                    run_id=run.id,
                    source="hackernews",
                    source_id=f"base_neg_{day}",
                    text_raw="Minor complaint",
                    published_at=day_time,
                    sentiment="negative",
                    status="done",
                )
            )

        # Today's surge: 10 mentions, 8 negative (80% negative share vs 10% baseline!)
        today_time = today_start + datetime.timedelta(hours=2)
        for idx in range(8):
            db_session.add(
                Mention(
                    keyword_id=kw.id,
                    run_id=run.id,
                    source="hackernews",
                    source_id=f"today_neg_{idx}",
                    text_raw="Disastrous bug outage crisis",
                    published_at=today_time,
                    sentiment="negative",
                    status="done",
                )
            )
        for idx in range(2):
            db_session.add(
                Mention(
                    keyword_id=kw.id,
                    run_id=run.id,
                    source="hackernews",
                    source_id=f"today_pos_{idx}",
                    text_raw="Still okay",
                    published_at=today_time,
                    sentiment="positive",
                    status="done",
                )
            )

        await db_session.commit()

        # Run alert engine
        alert = await evaluate_sentiment_spike_alerts(
            session=db_session,
            keyword_id=kw.id,
            keyword_term="AlertBrand",
            baseline_days=14,
            k_std_threshold=2.0,
            min_today_volume=5,
        )

        assert alert is not None
        assert alert.alert_type == "sentiment_spike"
        assert alert.details is not None
        assert alert.details["today_share"] >= 0.75  # 8/10 = 0.80
        assert alert.details["threshold"] < alert.details["today_share"]
        assert "Negative sentiment spike" in alert.message

    async def test_sentiment_alert_no_false_positive_on_normal_day(
        self, db_session: AsyncSession
    ) -> None:
        """BON-04: Verify NO alert is triggered when today's negative share is within normal baseline."""
        kw = await get_or_create_keyword(db_session, "CalmBrand")
        run = await create_collection_run(db_session, kw.id)
        now = datetime.datetime.now(datetime.UTC)
        today_start = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.UTC)

        # 14 days of ~10% negative
        for day in range(1, 14):
            day_time = today_start - datetime.timedelta(days=day, hours=12)
            for idx in range(9):
                db_session.add(
                    Mention(
                        keyword_id=kw.id,
                        run_id=run.id,
                        source="hackernews",
                        source_id=f"calm_base_{day}_{idx}",
                        text_raw="Normal product usage",
                        published_at=day_time,
                        sentiment="positive",
                        status="done",
                    )
                )
            db_session.add(
                Mention(
                    keyword_id=kw.id,
                    run_id=run.id,
                    source="hackernews",
                    source_id=f"calm_neg_{day}",
                    text_raw="Minor bug",
                    published_at=day_time,
                    sentiment="negative",
                    status="done",
                )
            )

        # Today: only 1 negative out of 10 mentions (normal)
        for idx in range(9):
            db_session.add(
                Mention(
                    keyword_id=kw.id,
                    run_id=run.id,
                    source="hackernews",
                    source_id=f"calm_today_pos_{idx}",
                    text_raw="Normal day today",
                    published_at=today_start + datetime.timedelta(hours=1),
                    sentiment="positive",
                    status="done",
                )
            )
        db_session.add(
            Mention(
                keyword_id=kw.id,
                run_id=run.id,
                source="hackernews",
                source_id="calm_today_neg",
                text_raw="One bug today",
                published_at=today_start + datetime.timedelta(hours=1),
                sentiment="negative",
                status="done",
            )
        )

        await db_session.commit()

        alert = await evaluate_sentiment_spike_alerts(
            session=db_session,
            keyword_id=kw.id,
            keyword_term="CalmBrand",
        )
        assert alert is None  # No alert!

    async def test_competitor_comparison_metrics(self, db_session: AsyncSession) -> None:
        """BON-02: Verify multi-brand comparative metrics and complaint themes."""
        kw1 = await get_or_create_keyword(db_session, "BrandAlpha")
        run1 = await create_collection_run(db_session, kw1.id)

        kw2 = await get_or_create_keyword(db_session, "BrandBeta")
        run2 = await create_collection_run(db_session, kw2.id)

        now = datetime.datetime.now(datetime.UTC)

        # Brand Alpha: mostly positive
        for i in range(8):
            db_session.add(
                Mention(
                    keyword_id=kw1.id,
                    run_id=run1.id,
                    source="googlenews",
                    source_id=f"alpha_{i}",
                    text_raw="Alpha has great build quality",
                    text_clean="Alpha has great build quality",
                    published_at=now,
                    sentiment="positive",
                    topic="general_feedback",
                    status="done",
                )
            )

        # Brand Beta: mostly negative complaints
        for i in range(6):
            db_session.add(
                Mention(
                    keyword_id=kw2.id,
                    run_id=run2.id,
                    source="googlenews",
                    source_id=f"beta_{i}",
                    text_raw=f"Beta battery overheating issue number {i}",
                    text_clean=f"Beta battery overheating issue number {i}",
                    published_at=now,
                    sentiment="negative",
                    topic="bug_issue",
                    status="done",
                )
            )

        await db_session.commit()

        res = await compare_keywords(db_session, ["BrandAlpha", "BrandBeta"])
        assert len(res.competitors) == 2

        alpha_stats = next(c for c in res.competitors if c.keyword == "BrandAlpha")
        beta_stats = next(c for c in res.competitors if c.keyword == "BrandBeta")

        assert alpha_stats.total_mentions == 8
        assert alpha_stats.positive_pct == 100.0
        assert beta_stats.total_mentions == 6
        assert beta_stats.negative_pct == 100.0
        assert len(beta_stats.common_complaints) >= 1
