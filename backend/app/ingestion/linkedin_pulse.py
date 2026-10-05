"""
LinkedIn Pulse & Professional Leadership Wire connector.
Monitors executive announcements, leadership statements, career moves, corporate restructuring,
and professional discourse across global business and professional publications.
No API key required.
"""

from __future__ import annotations

import datetime
import html
import logging
import re
import urllib.parse
from collections.abc import AsyncIterator

import feedparser

from app.config import Settings
from app.ingestion.base import SourceConnector
from app.ingestion.http_client import ResilientHttpClient
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
HTML_TAG_REGEX = re.compile(r"<[^>]+>")


class LinkedInPulseConnector(SourceConnector):
    """
    Connector for professional leadership discourse, career updates, and LinkedIn pulse topics.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "linkedin"

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
        Query professional wire feeds and executive search for the keyword.
        """
        # Targeted professional search query capturing executive, leadership, and workplace moves
        prof_query = f'"{keyword}" (executive OR leadership OR career OR CEO OR hiring OR "LinkedIn" OR founder OR layoff OR corporate)'
        encoded_query = urllib.parse.quote(prof_query)
        url = f"{GOOGLE_NEWS_RSS_URL}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

        try:
            response = await self.http_client.get(url, source_name=self.name)
            feed_content = response.text
        except Exception as exc:
            logger.error("[%s] Failed to fetch professional wire RSS: %s", self.name, exc)
            return

        parsed = feedparser.parse(feed_content)
        entries = parsed.entries or []
        yielded = 0

        for entry in entries:
            if yielded >= limit:
                break

            title = entry.get("title", "")
            raw_summary = entry.get("summary", "") or title
            clean_summary = HTML_TAG_REGEX.sub("", raw_summary)
            clean_summary = html.unescape(clean_summary).strip()
            link = entry.get("link", "")

            # Extract publisher / author
            publisher = "Professional Wire"
            source_tag = entry.get("source")
            if source_tag and isinstance(source_tag, dict):
                publisher = source_tag.get("title", publisher)
            elif " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                publisher = parts[1]

            combined_text = f"{title}. {clean_summary}" if clean_summary and clean_summary != title else title
            if not combined_text.strip():
                continue

            # Parse date
            pub_date = None
            if entry.get("published_parsed"):
                try:
                    pub_date = datetime.datetime(
                        *entry.published_parsed[:6], tzinfo=datetime.UTC
                    )
                except Exception:
                    pub_date = None

            if since and pub_date and pub_date < since:
                continue

            entry_id = entry.get("id") or link or f"prof_{yielded}"

            yield RawMention(
                source=self.name,
                source_id=f"li_{abs(hash(entry_id)) % 100000000}",
                url=link,
                canonical_url=link,
                title=title,
                text=combined_text,
                author=publisher,
                published_at=pub_date,
                engagement={"publisher": publisher},
                extra={"is_professional_wire": True, "feed": "business_leadership"},
                keyword=keyword,
            )
            yielded += 1
