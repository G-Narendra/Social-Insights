"""
Reddit source connector using official Reddit OAuth API.
Complies strictly with Reddit terms of service:
- Uses official OAuth application flow (client_credentials grant).
- If credentials are missing, gracefully disables itself and logs instructions.
- Never scrapes Reddit HTML directly.
"""

from __future__ import annotations

import datetime
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import Settings
from app.ingestion.base import ConnectorAuthError, SourceConnector
from app.ingestion.http_client import ResilientHttpClient
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)

REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_OAUTH_API_BASE = "https://oauth.reddit.com"


class RedditConnector(SourceConnector):
    """
    Connector for Reddit discussions via official OAuth API.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        user_agent: str | None = None,
        http_client: ResilientHttpClient | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent or "SocialInsightsApp/1.0 (social listening assignment)"
        self.http_client = http_client or ResilientHttpClient(user_agent=self.user_agent)
        self._token: str | None = None
        self._token_expiry: datetime.datetime | None = None

    @property
    def name(self) -> str:
        return "reddit"

    @property
    def requires_key(self) -> bool:
        return True

    def is_enabled(self, settings: Settings) -> bool:
        """Check if Reddit API credentials are provided in settings."""
        has_creds = bool(settings.reddit_client_id and settings.reddit_client_secret)
        if not has_creds:
            logger.info(
                "[%s] Connector disabled: REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET not configured",
                self.name,
            )
        return has_creds

    async def _get_access_token(self) -> str:
        """Acquire or reuse valid OAuth access token."""
        now = datetime.datetime.now(datetime.UTC)
        if self._token and self._token_expiry and now < self._token_expiry:
            return self._token

        if not self.client_id or not self.client_secret:
            raise ConnectorAuthError(self.name, "Missing Reddit client_id or client_secret")

        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        data = {"grant_type": "client_credentials"}
        headers = {"User-Agent": self.user_agent}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(REDDIT_AUTH_URL, auth=auth, data=data, headers=headers)
                res.raise_for_status()
                token_data = res.json()
        except Exception as exc:
            raise ConnectorAuthError(
                self.name, f"Failed to authenticate with Reddit OAuth: {exc}"
            ) from exc

        self._token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        self._token_expiry = now + datetime.timedelta(seconds=expires_in - 60)
        return self._token

    async def search(
        self,
        keyword: str,
        since: datetime.datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[RawMention]:
        """
        Query Reddit search API for recent posts mentioning keyword.
        """
        try:
            token = await self._get_access_token()
        except Exception as exc:
            logger.warning("[%s] Skipping Reddit collection: %s", self.name, exc)
            return

        url = f"{REDDIT_OAUTH_API_BASE}/search"
        params: dict[str, Any] = {
            "q": keyword,
            "limit": min(limit, 100),
            "sort": "new",
            "type": "link",
        }
        headers = {
            "Authorization": f"bearer {token}",
            "User-Agent": self.user_agent,
        }

        try:
            response = await self.http_client.get(
                url, params=params, headers=headers, source_name=self.name
            )
            data = response.json()
        except Exception as exc:
            logger.error("[%s] Search request failed: %s", self.name, exc)
            return

        children = data.get("data", {}).get("children", [])
        yielded = 0

        for child in children:
            if yielded >= limit:
                break

            post = child.get("data", {})
            post_id = post.get("id")
            if not post_id:
                continue

            title = post.get("title", "")
            selftext = post.get("selftext", "")
            full_text = f"{title}\n{selftext}".strip() if selftext else title

            if not full_text.strip():
                continue

            permalink = post.get("permalink")
            url = f"https://www.reddit.com{permalink}" if permalink else post.get("url")
            author = post.get("author")
            subreddit = post.get("subreddit")

            pub_date = None
            if post.get("created_utc"):
                pub_date = datetime.datetime.fromtimestamp(post["created_utc"], tz=datetime.UTC)

            if since and pub_date and pub_date < since:
                continue

            engagement = {
                "score": post.get("score") or 0,
                "num_comments": post.get("num_comments") or 0,
                "upvote_ratio": post.get("upvote_ratio") or 0.0,
            }
            extra = {
                "subreddit": subreddit,
                "domain": post.get("domain"),
                "is_video": post.get("is_video", False),
            }

            yield RawMention(
                source=self.name,
                source_id=f"t3_{post_id}",
                url=url,
                canonical_url=url,
                title=title,
                text=full_text,
                author=f"u/{author}" if author else None,
                published_at=pub_date,
                engagement=engagement,
                extra=extra,
                keyword=keyword,
            )
            yielded += 1
