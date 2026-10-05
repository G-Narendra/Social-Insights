"""
GitHub issues, PRs, and developer discussions connector.
Retrieves open-source discussions, technical feedback, bug reports, and community sentiment
for brands, software products, and prominent tech figures.
No mandatory API key required.
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

GITHUB_SEARCH_URL = "https://api.github.com/search/issues"


class GitHubConnector(SourceConnector):
    """
    Connector for GitHub issues, pull requests, and community technical discussions.
    """

    def __init__(self, http_client: ResilientHttpClient | None = None) -> None:
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "github"

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
        Query GitHub Search API for issues and discussions mentioning the keyword.
        """
        params: dict[str, Any] = {
            "q": f"{keyword} in:title,body",
            "sort": "updated",
            "order": "desc",
            "per_page": min(limit, 40),
        }

        try:
            response = await self.http_client.get(
                GITHUB_SEARCH_URL,
                params=params,
                source_name=self.name,
            )
            data = response.json()
        except Exception as exc:
            logger.warning("[%s] GitHub query failed or rate-limited: %s", self.name, exc)
            return

        items = data.get("items", [])
        yielded = 0

        for item in items:
            if yielded >= limit:
                break

            issue_id = str(item.get("id") or "")
            if not issue_id:
                continue

            title = item.get("title", "")
            raw_body = item.get("body") or ""
            raw_text = f"{title}\n\n{raw_body}".strip() if raw_body else title

            if not raw_text.strip():
                continue

            url = item.get("html_url") or f"https://github.com/search?q={keyword}"
            author = item.get("user", {}).get("login") or "github-user"

            pub_date = None
            if item.get("created_at"):
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        item["created_at"].replace("Z", "+00:00")
                    )
                except ValueError:
                    pub_date = None

            if since and pub_date and pub_date < since:
                continue

            engagement = {
                "comments": item.get("comments", 0),
                "reactions": item.get("reactions", {}).get("total_count", 0),
            }

            yield RawMention(
                source=self.name,
                source_id=f"gh_{issue_id}",
                url=url,
                canonical_url=url,
                title=title,
                text=raw_text,
                author=author,
                published_at=pub_date,
                engagement=engagement,
                extra={
                    "state": item.get("state"),
                    "repository_url": item.get("repository_url"),
                },
                keyword=keyword,
            )
            yielded += 1
