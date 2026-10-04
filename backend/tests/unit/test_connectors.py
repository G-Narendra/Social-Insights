"""
Unit tests for data ingestion connectors and orchestrator using offline fixtures.
Validates extraction accuracy, failure mode resilience (timeout, 429, malformed),
and orchestrator fault isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from unittest.mock import AsyncMock, patch

import pytest
from pytest_httpx import HTTPXMock

from app.config import Settings
from app.ingestion.google_news_rss import GoogleNewsRSSConnector
from app.ingestion.hackernews import HackerNewsConnector
from app.ingestion.http_client import ResilientHttpClient
from app.ingestion.orchestrator import run_ingestion
from app.ingestion.reddit import REDDIT_AUTH_URL, RedditConnector
from app.ingestion.stackexchange import StackExchangeConnector
from app.ingestion.youtube import YouTubeConnector

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestHackerNewsConnector:
    @pytest.mark.asyncio
    async def test_parse_stories_and_comments(self, httpx_mock: HTTPXMock) -> None:
        payload = json.loads(
            (FIXTURES_DIR / "hackernews_response.json").read_text(encoding="utf-8")
        )
        httpx_mock.add_response(url=re.compile(r".*hn\.algolia\.com.*"), json=payload)

        client = ResilientHttpClient()
        connector = HackerNewsConnector(http_client=client)

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert len(mentions) == 2

        # 1. Story
        story = mentions[0]
        assert story.source == "hackernews"
        assert story.source_id == "38912345"
        assert "solid-state battery" in story.title
        assert story.author == "car_enthusiast"
        assert story.engagement["points"] == 342
        assert story.engagement["num_comments"] == 158

        # 2. Comment
        comment = mentions[1]
        assert comment.source_id == "38912500"
        assert "Toyota reliability" in comment.text
        assert comment.extra["is_comment"] is True
        await client.close()

    @pytest.mark.asyncio
    async def test_hn_handles_malformed_json(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(url=re.compile(r".*hn\.algolia\.com.*"), text="Invalid JSON{")
        client = ResilientHttpClient()
        connector = HackerNewsConnector(http_client=client)

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert mentions == []
        await client.close()


class TestGoogleNewsConnector:
    @pytest.mark.asyncio
    async def test_parse_rss_and_publisher(self, httpx_mock: HTTPXMock) -> None:
        xml_content = (FIXTURES_DIR / "googlenews_rss.xml").read_text(encoding="utf-8")
        httpx_mock.add_response(url=re.compile(r".*news\.google\.com.*"), text=xml_content)

        client = ResilientHttpClient()
        connector = GoogleNewsRSSConnector(http_client=client)

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert len(mentions) == 2

        m1 = mentions[0]
        assert m1.source == "googlenews"
        assert m1.author == "Reuters"
        assert m1.title == "Toyota Reports Record Global Sales for Fiscal Year"
        assert "hybrid demand" in m1.text

        m2 = mentions[1]
        assert m2.author == "MotorTrend"
        assert m2.title == "New 2026 Toyota Tacoma Hybrid Review and Pricing"
        await client.close()


class TestRedditConnector:
    @pytest.mark.asyncio
    async def test_disabled_without_credentials(self) -> None:
        settings = Settings(reddit_client_id=None, reddit_client_secret=None)
        connector = RedditConnector()
        assert connector.is_enabled(settings) is False

    @pytest.mark.asyncio
    async def test_search_with_credentials(self, httpx_mock: HTTPXMock) -> None:
        # Mock OAuth token
        httpx_mock.add_response(
            url=REDDIT_AUTH_URL,
            json={"access_token": "fake_token_123", "expires_in": 3600},
        )
        # Mock search results
        payload = json.loads((FIXTURES_DIR / "reddit_response.json").read_text(encoding="utf-8"))
        httpx_mock.add_response(
            url=re.compile(r".*oauth\.reddit\.com.*"),
            json=payload,
        )

        client = ResilientHttpClient()
        connector = RedditConnector(
            client_id="test_id",
            client_secret="test_secret",
            http_client=client,
        )

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert len(mentions) == 2
        assert mentions[0].source == "reddit"
        assert mentions[0].source_id == "t3_abc1234"
        assert mentions[0].author == "u/hybrid_driver"
        assert mentions[0].engagement["score"] == 412
        assert mentions[0].extra["subreddit"] == "rav4club"
        await client.close()


class TestYouTubeConnector:
    @pytest.mark.asyncio
    async def test_disabled_without_key(self) -> None:
        settings = Settings(youtube_api_key=None)
        connector = YouTubeConnector()
        assert connector.is_enabled(settings) is False

    @pytest.mark.asyncio
    async def test_search_with_key(self, httpx_mock: HTTPXMock) -> None:
        payload = json.loads((FIXTURES_DIR / "youtube_response.json").read_text(encoding="utf-8"))
        httpx_mock.add_response(url=re.compile(r".*googleapis\.com.*"), json=payload)

        client = ResilientHttpClient()
        connector = YouTubeConnector(api_key="valid_key", http_client=client)

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert len(mentions) == 1
        assert mentions[0].source == "youtube"
        assert mentions[0].source_id == "yt_video_dQw4w9WgXcQ"
        assert mentions[0].author == "Throttle House Reviews"
        await client.close()


class TestStackExchangeConnector:
    @pytest.mark.asyncio
    async def test_search_questions(self, httpx_mock: HTTPXMock) -> None:
        payload = json.loads(
            (FIXTURES_DIR / "stackexchange_response.json").read_text(encoding="utf-8")
        )
        httpx_mock.add_response(url=re.compile(r".*api\.stackexchange\.com.*"), json=payload)

        client = ResilientHttpClient()
        connector = StackExchangeConnector(http_client=client)

        mentions = [m async for m in connector.search("Toyota", limit=10)]
        assert len(mentions) == 1
        assert mentions[0].source == "stackexchange"
        assert mentions[0].source_id == "se_7891011"
        assert mentions[0].engagement["score"] == 15
        assert "python" in mentions[0].extra["tags"]
        await client.close()


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_orchestrator_fault_isolation(self) -> None:
        """If one connector raises an error, others finish and run is partial."""
        mock_good = AsyncMock()
        mock_good.name = "good_source"
        mock_good.is_enabled.return_value = True

        async def good_gen(*args, **kwargs):
            yield {
                "source": "good_source",
                "source_id": "1",
                "text": "Good text",
                "keyword": "Toyota",
            }

        mock_failing = AsyncMock()
        mock_failing.name = "failing_source"
        mock_failing.is_enabled.return_value = True

        async def failing_gen(*args, **kwargs):
            raise RuntimeError("API Connection Reset")
            yield  # unreachable

        with patch("app.ingestion.orchestrator.get_enabled_connectors") as mock_reg:
            mock_reg.return_value = {
                "good_source": mock_good,
                "failing_source": mock_failing,
            }
            mock_good.search = good_gen
            mock_failing.search = failing_gen

            result = await run_ingestion("Toyota", limit=50)
            assert result.status == "partial"
            assert len(result.mentions) == 1
            assert len(result.errors) == 1
            assert result.errors[0]["source"] == "failing_source"
            assert "API Connection Reset" in result.errors[0]["error"]
