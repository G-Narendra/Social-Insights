"""
Google News RSS source connector using public RSS search feeds.
Parses RSS feeds via feedparser, extracting headlines, publishers, and publication dates.
No API key required.
"""

from __future__ import annotations

import datetime
import logging
import urllib.parse
from collections.abc import AsyncIterator

import feedparser

from app.config import Settings
from app.ingestion.base import SourceConnector
from app.ingestion.http_client import ResilientHttpClient
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"


class GoogleNewsRSSConnector(SourceConnector):
    """
    Connector for Google News RSS search feeds.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "googlenews"

    @property
    def requires_key(self) -> bool:
        return False

    def is_enabled(self, settings: Settings) -> bool:
        return True

    async def search(
        self,
        keyword: str,
        since: datetime.datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[RawMention]:
        """
        Fetch and parse Google News RSS feed for the specified keyword.
        """
        encoded_query = urllib.parse.quote(keyword)
        url = f"{GOOGLE_NEWS_RSS_URL}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        try:
            response = await self.http_client.get(url, source_name=self.name)
            feed_content = response.text
        except Exception as exc:
            logger.error("[%s] Failed to fetch Google News RSS: %s", self.name, exc)
            return

        # Parse with feedparser
        parsed = feedparser.parse(feed_content)
        entries = parsed.entries or []
        yielded = 0

        for entry in entries:
            if yielded >= limit:
                break

            title = entry.get("title", "")
            summary = entry.get("summary", "") or title
            link = entry.get("link", "")
            guid = entry.get("id") or link

            if not link or not summary.strip():
                continue

            # Extract publisher if format is "Headline - Publisher"
            publisher = None
            clean_title = title
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                clean_title = parts[0].strip()
                publisher = parts[1].strip()

            # Parse publication timestamp
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.UTC)

            # Filter by since if specified
            if since and pub_date and pub_date < since:
                continue

            yield RawMention(
                source=self.name,
                source_id=guid,
                url=link,
                canonical_url=link,
                title=clean_title,
                text=summary,
                author=publisher,
                published_at=pub_date,
                engagement={"views": 0},
                extra={"publisher": publisher},
                keyword=keyword,
            )
            yielded += 1
