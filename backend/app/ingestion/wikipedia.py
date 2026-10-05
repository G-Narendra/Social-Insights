"""
Wikipedia and Wikimedia knowledge connector.
Queries the public MediaWiki API to ingest encyclopedic updates, historical milestones,
biographical records, and controversy coverage for brands and public figures.
Requires zero API keys.
"""

from __future__ import annotations

import datetime
import html
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from app.config import Settings
from app.ingestion.base import SourceConnector
from app.ingestion.http_client import ResilientHttpClient
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
HTML_TAG_REGEX = re.compile(r"<[^>]+>")


class WikipediaConnector(SourceConnector):
    """
    Connector for global knowledge, biographical updates, and company histories from Wikipedia.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "wikipedia"

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
        Query MediaWiki search API for pages and snippets mentioning the keyword.
        """
        params: dict[str, Any] = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "utf8": "1",
            "format": "json",
            "srlimit": min(limit, 50),
        }

        try:
            response = await self.http_client.get(
                WIKIPEDIA_API_URL,
                params=params,
                source_name=self.name,
            )
            data = response.json()
        except Exception as exc:
            logger.error("[%s] Failed to query Wikipedia API: %s", self.name, exc)
            return

        search_results = data.get("query", {}).get("search", [])
        yielded = 0

        for item in search_results:
            if yielded >= limit:
                break

            page_id = str(item.get("pageid") or "")
            if not page_id:
                continue

            title = item.get("title", "")
            raw_snippet = item.get("snippet", "")
            # Clean HTML markup from snippet
            clean_text = HTML_TAG_REGEX.sub("", raw_snippet)
            clean_text = html.unescape(clean_text).strip()

            combined_text = f"{title}. {clean_text}" if clean_text else title
            if not combined_text.strip():
                continue

            url = f"https://en.wikipedia.org/?curid={page_id}"

            # Parse ISO timestamp
            pub_date = None
            if item.get("timestamp"):
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        item["timestamp"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pub_date = None

            if since and pub_date and pub_date < since:
                continue

            engagement = {
                "wordcount": item.get("wordcount", 0),
                "size": item.get("size", 0),
            }

            yield RawMention(
                source=self.name,
                source_id=f"wiki_{page_id}",
                url=url,
                canonical_url=url,
                title=title,
                text=combined_text,
                author="Wikipedia Contributors",
                published_at=pub_date,
                engagement=engagement,
                extra={"page_id": page_id, "size": item.get("size")},
                keyword=keyword,
            )
            yielded += 1
