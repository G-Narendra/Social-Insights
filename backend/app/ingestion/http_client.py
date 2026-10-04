"""
Resilient HTTP client for external social ingestion APIs.
Implements exponential backoff with jitter, Retry-After header parsing,
User-Agent compliance, and strict connection/read timeouts.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

import httpx

from app.ingestion.base import ConnectorNetworkError, ConnectorRateLimitError

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "SocialInsightsPlatform/1.0 (+https://github.com/social-insights/platform; "
    "open-source social listening bot)"
)


class ResilientHttpClient:
    """
    HTTP client wrapper providing retry policies, backoff jitter,
    and descriptive User-Agent headers.
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 12.0,
        max_retries: int = 3,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = httpx.Timeout(timeout, connect=5.0)
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or initialize singleton async client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        source_name: str = "http",
    ) -> httpx.Response:
        """
        Execute an HTTP GET request with automatic retry on 429 / 5xx.
        """
        client = await self.get_client()
        request_headers = {"User-Agent": self.user_agent}
        if headers:
            request_headers.update(headers)

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await client.get(url, params=params, headers=request_headers)

                # Handle rate limit (429)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_seconds = 2.0 * attempt + random.uniform(0.1, 0.5)
                    if retry_after and retry_after.isdigit():
                        wait_seconds = max(float(retry_after), wait_seconds)

                    if attempt < self.max_retries:
                        logger.warning(
                            "[%s] Rate limited (429). Retrying in %.2fs (attempt %d/%d)",
                            source_name,
                            wait_seconds,
                            attempt,
                            self.max_retries,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue
                    else:
                        raise ConnectorRateLimitError(
                            source=source_name,
                            message=f"Rate limit exceeded after {self.max_retries} attempts: {response.text[:200]}",
                        )

                # Retry on 5xx server errors
                if 500 <= response.status_code < 600:
                    wait_seconds = (2.0**attempt) + random.uniform(0.1, 0.5)
                    if attempt < self.max_retries:
                        logger.warning(
                            "[%s] Server error (%d). Retrying in %.2fs (attempt %d/%d)",
                            source_name,
                            response.status_code,
                            wait_seconds,
                            attempt,
                            self.max_retries,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue
                    else:
                        response.raise_for_status()

                # Raise for 4xx client errors (400, 401, 403, 404) immediately without retrying
                response.raise_for_status()
                return response

            except httpx.TimeoutException as exc:
                if attempt < self.max_retries:
                    wait_seconds = 1.0 * attempt + random.uniform(0.1, 0.3)
                    logger.warning(
                        "[%s] Timeout contacting %s. Retrying in %.2fs",
                        source_name,
                        url,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                else:
                    raise ConnectorNetworkError(
                        source=source_name,
                        message=f"Connection timed out for URL: {url}",
                        original_error=exc,
                    ) from exc

            except httpx.RequestError as exc:
                if attempt < self.max_retries:
                    wait_seconds = 1.0 * attempt + random.uniform(0.1, 0.3)
                    await asyncio.sleep(wait_seconds)
                else:
                    raise ConnectorNetworkError(
                        source=source_name,
                        message=f"Network request error: {exc}",
                        original_error=exc,
                    ) from exc

        raise ConnectorNetworkError(source=source_name, message=f"Failed to fetch {url}")
