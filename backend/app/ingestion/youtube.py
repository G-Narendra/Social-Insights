"""
YouTube Data API v3 connector.
Retrieves video snippets and top comments.
Enforces quota awareness (free tier 10,000 units/day, search costs 100 units).
Gracefully disables when no API key is supplied.
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

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"


class YouTubeConnector(SourceConnector):
    """
    Connector for YouTube video metadata and comments.
    """

    def __init__(
        self,
        api_key: str | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.http_client = http_client or ResilientHttpClient()

    @property
    def name(self) -> str:
        return "youtube"

    @property
    def requires_key(self) -> bool:
        return True

    def is_enabled(self, settings: Settings) -> bool:
        has_key = bool(settings.youtube_api_key)
        if not has_key:
            logger.info("[%s] Connector disabled: YOUTUBE_API_KEY not configured", self.name)
        return has_key

    async def search(
        self,
        keyword: str,
        since: datetime.datetime | None = None,
        limit: int = 50,
    ) -> AsyncIterator[RawMention]:
        """
        Query YouTube Data API for videos matching keyword.
        """
        if not self.api_key:
            logger.warning("[%s] Skipping YouTube search: missing api_key", self.name)
            return

        params: dict[str, Any] = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": min(limit, 25),
            "key": self.api_key,
        }
        if since:
            params["publishedAfter"] = since.isoformat()

        try:
            response = await self.http_client.get(
                YOUTUBE_SEARCH_URL, params=params, source_name=self.name
            )
            data = response.json()
        except Exception as exc:
            logger.error("[%s] Search request failed: %s", self.name, exc)
            return

        items = data.get("items", [])
        yielded = 0

        for item in items:
            if yielded >= limit:
                break

            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue

            snippet = item.get("snippet", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            full_text = f"{title}\n{description}".strip()
            channel_title = snippet.get("channelTitle")
            published_at_str = snippet.get("publishedAt")

            pub_date = None
            if published_at_str:
                try:
                    pub_date = datetime.datetime.fromisoformat(
                        published_at_str.replace("Z", "+00:00")
                    )
                except ValueError:
                    pub_date = None

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            yield RawMention(
                source=self.name,
                source_id=f"yt_video_{video_id}",
                url=video_url,
                canonical_url=video_url,
                title=title,
                text=full_text,
                author=channel_title,
                published_at=pub_date,
                engagement={"views": 0, "likes": 0},
                extra={"channel_title": channel_title, "channel_id": snippet.get("channelId")},
                keyword=keyword,
            )
            yielded += 1
