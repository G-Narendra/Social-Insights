"""
Abstract base class and error hierarchies for all source connectors.
Every data source (Hacker News, Google News, Reddit, YouTube, Stack Exchange)
implements this interface.
"""

from __future__ import annotations

import abc
import datetime
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from app.schemas.mentions import RawMention

if TYPE_CHECKING:
    from app.config import Settings


class ConnectorError(Exception):
    """Base exception for all connector-related failures."""

    def __init__(self, source: str, message: str, original_error: Exception | None = None) -> None:
        self.source = source
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{source}] {message}")


class ConnectorRateLimitError(ConnectorError):
    """Raised when an external API returns HTTP 429 or quota exhaustion."""

    pass


class ConnectorAuthError(ConnectorError):
    """Raised when authentication credentials are invalid or missing."""

    pass


class ConnectorNetworkError(ConnectorError):
    """Raised when network connection fails or times out."""

    pass


class SourceConnector(abc.ABC):
    """
    Abstract contract for ingesting mentions from external public sources.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Unique identifier for this connector (e.g. 'hackernews', 'googlenews')."""
        pass

    @property
    @abc.abstractmethod
    def requires_key(self) -> bool:
        """Whether this connector requires an API key/secret to operate."""
        pass

    @abc.abstractmethod
    def is_enabled(self, settings: Settings) -> bool:
        """Determine if this connector can run given current system configuration."""
        pass

    @abc.abstractmethod
    async def search(
        self,
        keyword: str,
        since: datetime.datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[RawMention]:
        """
        Yield RawMention items matching keyword.
        Must handle errors gracefully and never yield partial/corrupt objects.
        """
        pass
