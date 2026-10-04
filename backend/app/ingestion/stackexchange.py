"""
Stack Exchange public API source connector.
Queries Stack Overflow discussions and questions without requiring an API key.
Handles Stack Exchange throttling and backoff notices.
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

STACK_EXCHANGE_SEARCH_URL = "https://api.stackexchange.com/2.3/search/advanced"


class StackExchangeConnector(SourceConnector):
    """
    Connector for Stack Exchange / Stack Overflow developer discussions.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "stackexchange"

    @property
    def requires_key(self) -> bool:
        return False

    def is_enabled(self, settings: Settings) -> bool:
        return True

    async def search(
        self,
        keyword: str,
        since: datetime.datetime | None = None,
        limit: int = 50,
    ) -> AsyncIterator[RawMention]:
        """
        Query Stack Exchange search API for questions mentioning keyword.
        """
        params: dict[str, Any] = {
            "q": keyword,
            "site": "stackoverflow",
            "pagesize": min(limit, 30),
            "order": "desc",
            "sort": "creation",
            "filter": "default",
        }
        if since:
            params["fromdate"] = int(since.timestamp())

        try:
            response = await self.http_client.get(
                STACK_EXCHANGE_SEARCH_URL, params=params, source_name=self.name
            )
            data = response.json()
        except Exception as exc:
            logger.error("[%s] Search request failed: %s", self.name, exc)
            return

        # Check for throttle backoff
        if "backoff" in data:
            logger.warning(
                "[%s] Stack Exchange requested backoff for %d seconds",
                self.name,
                data["backoff"],
            )

        items = data.get("items", [])
        yielded = 0

        for item in items:
            if yielded >= limit:
                break

            q_id = str(item.get("question_id") or "")
            if not q_id:
                continue

            title = item.get("title", "")
            link = item.get("link", "")
            owner = item.get("owner", {})
            author = owner.get("display_name")

            pub_date = None
            if item.get("creation_date"):
                pub_date = datetime.datetime.fromtimestamp(item["creation_date"], tz=datetime.UTC)

            engagement = {
                "score": item.get("score") or 0,
                "answer_count": item.get("answer_count") or 0,
                "view_count": item.get("view_count") or 0,
                "is_answered": item.get("is_answered", False),
            }
            extra = {
                "tags": item.get("tags", []),
                "reputation": owner.get("reputation"),
            }

            yield RawMention(
                source=self.name,
                source_id=f"se_{q_id}",
                url=link,
                canonical_url=link,
                title=title,
                text=title,  # default filter gives title
                author=author,
                published_at=pub_date,
                engagement=engagement,
                extra=extra,
                keyword=keyword,
            )
            yielded += 1
