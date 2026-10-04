"""
Hacker News source connector using the public Algolia Search API.
Public API requires no API key. Retrieves both stories and discussion comments.
"""

from __future__ import annotations

import datetime
import logging
from collections.abc import AsyncIterator
from typing import Any

from app.config import Settings
from app.ingestion.base import SourceConnector
from app.ingestion.http_client import ResilientHttpClient
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class HackerNewsConnector(SourceConnector):
    """
    Connector for Hacker News stories and comments via Algolia.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "hackernews"

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
        Query Algolia API for stories and comments mentioning the keyword.
        """
        params: dict[str, Any] = {
            "query": keyword,
            "hitsPerPage": min(limit, 100),
            "tags": "(story,comment)",
        }

        if since:
            since_ts = int(since.timestamp())
            params["numericFilters"] = f"created_at_i>{since_ts}"

        try:
            response = await self.http_client.get(
                HN_SEARCH_URL,
                params=params,
                source_name=self.name,
            )
            data = response.json()
        except Exception as exc:
            logger.error("[%s] Failed to query Algolia API: %s", self.name, exc)
            return

        hits = data.get("hits", [])
        yielded = 0

        for hit in hits:
            if yielded >= limit:
                break

            obj_id = str(hit.get("objectID") or "")
            if not obj_id:
                continue

            # Text can be in story_text, comment_text, or fallback to title
            title = hit.get("title") or hit.get("story_title")
            raw_text = hit.get("comment_text") or hit.get("story_text") or title or ""

            # Skip empty mentions
            if not raw_text.strip():
                continue

            # Build URL: external story URL if available, else HN discussion thread
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={obj_id}"
            author = hit.get("author")

            # Parse publication timestamp
            pub_date = None
            if hit.get("created_at_i"):
                pub_date = datetime.datetime.fromtimestamp(hit["created_at_i"], tz=datetime.UTC)
            elif hit.get("created_at"):
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        hit["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pub_date = None

            engagement = {
                "points": hit.get("points") or 0,
                "num_comments": hit.get("num_comments") or 0,
            }

            extra = {
                "parent_id": hit.get("parent_id"),
                "story_id": hit.get("story_id"),
                "is_comment": "comment" in hit.get("_tags", []),
            }

            yield RawMention(
                source=self.name,
                source_id=obj_id,
                url=url,
                canonical_url=url,
                title=title,
                text=raw_text,
                author=author,
                published_at=pub_date,
                engagement=engagement,
                extra=extra,
                keyword=keyword,
            )
            yielded += 1
