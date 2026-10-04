"""
Unit tests for AI/ML modules.
Validates sentiment gating, topic prototype centroids, template summarizer,
and LLM client fallbacks.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.ml.llm_client import LLMClient
from app.ml.sentiment import SentimentResult, _rule_fallback_sentiment
from app.ml.summarizer import (
    _generate_template_insights,
    _generate_template_summary,
    compute_data_fingerprint,
)
from app.ml.topics import TOPIC_SET, _rule_fallback_topic
from app.schemas.stats import (
    OverviewStatsResponse,
    QualityMetrics,
    SentimentBreakdown,
    TopicCount,
)


class TestSentimentUnit:
    def test_rule_fallback_sentiment_positive(self) -> None:
        res = _rule_fallback_sentiment("I love this car, it is fantastic and reliable")
        assert res.label == "positive"
        assert res.score > 0.5
        assert res.is_low_confidence is False

    def test_rule_fallback_sentiment_negative(self) -> None:
        res = _rule_fallback_sentiment("Terrible experience, broken engine and awful service")
        assert res.label == "negative"
        assert res.score > 0.5

    def test_rule_fallback_sentiment_neutral(self) -> None:
        res = _rule_fallback_sentiment("The vehicle has four wheels and headlights.")
        assert res.label == "neutral"


class TestTopicsUnit:
    def test_all_topic_set_valid(self) -> None:
        assert len(TOPIC_SET) == 8
        assert "pricing" in TOPIC_SET
        assert "quality" in TOPIC_SET
        assert "customer_service" in TOPIC_SET

    def test_rule_fallback_topic(self) -> None:
        res_price = _rule_fallback_topic("The MSRP and monthly lease cost is high")
        assert res_price.topic == "pricing"

        res_quality = _rule_fallback_topic("The engine is durable and highly reliable")
        assert res_quality.topic == "quality"

        res_other = _rule_fallback_topic("The sky was blue this morning")
        assert res_other.topic == "other"


class TestSummarizerUnit:
    def test_fingerprint_computation(self) -> None:
        fp1 = compute_data_fingerprint("Toyota", 100, 50, 20, 105)
        fp2 = compute_data_fingerprint("Toyota", 100, 50, 20, 105)
        fp3 = compute_data_fingerprint("Toyota", 101, 50, 20, 106)
        assert fp1 == fp2
        assert fp1 != fp3

    def test_template_summary_synthesis(self) -> None:
        stats = OverviewStatsResponse(
            keyword="Toyota",
            keyword_id=1,
            total_mentions=150,
            sentiment=SentimentBreakdown(
                positive=90,
                neutral=45,
                negative=15,
                positive_pct=60.0,
                neutral_pct=30.0,
                negative_pct=10.0,
            ),
            top_topics=[
                TopicCount(topic="quality", count=80, percentage=53.3),
                TopicCount(topic="features", count=40, percentage=26.7),
            ],
            sources={"reddit": 100, "hackernews": 50},
            quality=QualityMetrics(total_collected=180, total_kept=150, total_dropped=30),
        )

        samples = [
            (1, "Great reliable car", "positive", "quality"),
            (2, "Wish it had faster charging", "neutral", "features"),
            (3, "Overpriced accessories", "negative", "pricing"),
        ]

        summary_text = _generate_template_summary("Toyota", stats, samples)
        assert "Toyota" in summary_text
        assert "predominantly positive" in summary_text
        assert "60.0%" in summary_text
        assert "quality" in summary_text

        insights = _generate_template_insights(samples, stats)
        assert len(insights.positive_themes) >= 1
        assert len(insights.pain_points) >= 1
        assert len(insights.requested_features) >= 1


class TestLLMClientUnit:
    @pytest.mark.asyncio
    async def test_llm_client_unavailable_returns_none(self) -> None:
        client = LLMClient()
        client.api_key = None
        client._client = None

        assert client.is_available is False
        res = await client.generate_json("system", "user")
        assert res is None
