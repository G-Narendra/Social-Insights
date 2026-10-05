"""
Integration tests for FastAPI REST endpoints.
Uses AsyncClient against isolated in-memory test databases.
"""

from __future__ import annotations

import datetime
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.main import app
from app.schemas.mentions import RawMention
from app.services.keyword_service import get_or_create_keyword
from app.services.mention_service import update_mention_enrichment, upsert_mention


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Yield test HTTP client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient) -> None:
        res = await async_client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


class TestKeywordEndpoints:
    @pytest.mark.asyncio
    async def test_create_and_list_keywords(self, async_client: AsyncClient) -> None:
        # Create
        res = await async_client.post(
            "/api/keywords",
            json={"term": "Tesla", "aliases": ["TSLA"], "context_hint": "EV automaker"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["term"] == "Tesla"
        assert data["aliases"] == ["TSLA"]

        # List
        list_res = await async_client.get("/api/keywords")
        assert list_res.status_code == 200
        kw_list = list_res.json()
        assert any(k["term"] == "Tesla" for k in kw_list)


class TestCollectionEndpoints:
    @pytest.mark.asyncio
    async def test_trigger_collection_and_idempotency(self, async_client: AsyncClient) -> None:
        with patch("app.api.collect.execute_collection_pipeline") as mock_pipeline:
            res = await async_client.post(
                "/api/collect",
                json={"keyword": "Toyota", "limit": 50},
            )
            assert res.status_code == 202
            data = res.json()
            assert "run_id" in data
            run_id = data["run_id"]
            mock_pipeline.assert_called_once()

            # Duplicate immediate trigger should return existing run_id
            res_dup = await async_client.post(
                "/api/collect",
                json={"keyword": "Toyota", "limit": 50},
            )
            assert res_dup.status_code == 202
            assert res_dup.json()["run_id"] == run_id

            # Query run status
            poll_res = await async_client.get(f"/api/runs/{run_id}")
            assert poll_res.status_code == 200
            poll_data = poll_res.json()
            assert poll_data["id"] == run_id

    @pytest.mark.asyncio
    async def test_invalid_keyword_returns_422(self, async_client: AsyncClient) -> None:
        # Single char keyword
        res = await async_client.post("/api/collect", json={"keyword": "x"})
        assert res.status_code == 422
        assert "error" in res.json()
        assert res.json()["error"]["code"] == "validation_error"


class TestMentionsAndStatsEndpoints:
    @pytest_asyncio.fixture(autouse=True)
    async def seed_data(self, db_session: AsyncSession) -> None:
        kw = await get_or_create_keyword(db_session, "Apple")
        # Add 2 mentions
        m1, _ = await upsert_mention(
            db_session,
            kw.id,
            run_id=1,
            raw=RawMention(
                source="hackernews",
                source_id="hn_apple_1",
                title="Apple M4 Mac Review",
                text="The Apple M4 Mac is fantastic with great battery life.",
                keyword="Apple",
                published_at=datetime.datetime(2026, 1, 10, 10, 0),
            ),
        )
        await update_mention_enrichment(
            db_session,
            m1.id,
            sentiment="positive",
            sentiment_score=0.95,
            topic="product",
            topic_score=0.90,
        )

        m2, _ = await upsert_mention(
            db_session,
            kw.id,
            run_id=1,
            raw=RawMention(
                source="reddit",
                source_id="rd_apple_2",
                title="Apple repair cost",
                text="Apple screen repair is too expensive.",
                keyword="Apple",
                published_at=datetime.datetime(2026, 1, 11, 11, 0),
            ),
        )
        await update_mention_enrichment(
            db_session,
            m2.id,
            sentiment="negative",
            sentiment_score=0.88,
            topic="pricing",
            topic_score=0.85,
        )

    @pytest.mark.asyncio
    async def test_get_mentions_and_filters(self, async_client: AsyncClient) -> None:
        res = await async_client.get("/api/mentions?keyword=Apple")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # Filter by sentiment
        neg_res = await async_client.get("/api/mentions?keyword=Apple&sentiment=negative")
        assert neg_res.status_code == 200
        assert neg_res.json()["total"] == 1
        assert "expensive" in neg_res.json()["items"][0]["text_raw"]

    @pytest.mark.asyncio
    async def test_get_stats_overview_and_timeseries(self, async_client: AsyncClient) -> None:
        res = await async_client.get("/api/stats/overview?keyword=Apple")
        assert res.status_code == 200
        stats = res.json()
        assert stats["total_mentions"] == 2
        assert stats["sentiment"]["positive"] == 1
        assert stats["sentiment"]["negative"] == 1

        ts_res = await async_client.get("/api/stats/timeseries?keyword=Apple&interval=day")
        assert ts_res.status_code == 200
        ts_data = ts_res.json()
        assert len(ts_data["buckets"]) >= 1

    @pytest.mark.asyncio
    async def test_summary_and_insights(self, async_client: AsyncClient) -> None:
        res = await async_client.get("/api/summary?keyword=Apple")
        assert res.status_code == 200
        data = res.json()
        assert "content" in data
        assert len(data["content"]) > 20

        # Insights endpoint
        ins_res = await async_client.get("/api/insights?keyword=Apple")
        assert ins_res.status_code == 200

    @pytest.mark.asyncio
    async def test_competitor_comparison(self, async_client: AsyncClient) -> None:
        res = await async_client.get("/api/compare?keywords=Apple,Microsoft")
        assert res.status_code == 200
        data = res.json()
        assert len(data["competitors"]) == 2
        assert data["competitors"][0]["keyword"] == "Apple"

    @pytest.mark.asyncio
    async def test_simulate_and_resolve_alert(self, async_client: AsyncClient) -> None:
        sim_res = await async_client.post(
            "/api/alerts/simulate",
            json={"keyword": "Apple", "scenario": "sentiment_spike"},
        )
        assert sim_res.status_code == 200
        alert_data = sim_res.json()
        assert alert_data["alert_type"] == "sentiment_spike"
        assert alert_data["severity"] == "critical"
        alert_id = alert_data["id"]

        # Verify it appears in active alerts
        list_res = await async_client.get("/api/alerts?keyword=Apple")
        assert list_res.status_code == 200
        assert any(a["id"] == alert_id for a in list_res.json())

        # Resolve the alert
        resolve_res = await async_client.post(f"/api/alerts/{alert_id}/resolve")
        assert resolve_res.status_code == 200
        assert resolve_res.json()["alert_id"] == alert_id

        # Verify it is no longer in active alerts
        list_after = await async_client.get("/api/alerts?keyword=Apple")
        assert not any(a["id"] == alert_id for a in list_after.json())


class TestInternalEndpoints:
    @pytest.mark.asyncio
    async def test_internal_ingest_without_secret_fails(self, async_client: AsyncClient) -> None:
        res = await async_client.post("/internal/ingest")
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_internal_ingest_with_secret_succeeds(self, async_client: AsyncClient) -> None:
        settings = get_settings()
        res = await async_client.post(
            "/internal/ingest",
            headers={"X-Internal-Secret": settings.internal_secret},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "success"
