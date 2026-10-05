"""
Connector Registry for the Ingestion layer.
Enables pluggable data sources: adding a new source requires only creating
one connector class and registering it here.
"""

from __future__ import annotations

import logging

from app.config import Settings, get_settings
from app.ingestion.base import SourceConnector
from app.ingestion.github import GitHubConnector
from app.ingestion.google_news_rss import GoogleNewsRSSConnector
from app.ingestion.hackernews import HackerNewsConnector
from app.ingestion.linkedin_pulse import LinkedInPulseConnector
from app.ingestion.reddit import RedditConnector
from app.ingestion.stackexchange import StackExchangeConnector
from app.ingestion.wikipedia import WikipediaConnector
from app.ingestion.youtube import YouTubeConnector

logger = logging.getLogger(__name__)


def create_all_connectors(settings: Settings | None = None) -> dict[str, SourceConnector]:
    """
    Instantiate all supported source connectors with appropriate credentials.
    """
    cfg = settings or get_settings()

    connectors: dict[str, SourceConnector] = {
        "hackernews": HackerNewsConnector(),
        "googlenews": GoogleNewsRSSConnector(),
        "wikipedia": WikipediaConnector(),
        "github": GitHubConnector(),
        "linkedin": LinkedInPulseConnector(),
        "reddit": RedditConnector(
            client_id=cfg.reddit_client_id,
            client_secret=cfg.reddit_client_secret,
            user_agent=cfg.reddit_user_agent,
        ),
        "youtube": YouTubeConnector(api_key=cfg.youtube_api_key),
        "stackexchange": StackExchangeConnector(),
    }
    return connectors


def get_enabled_connectors(
    settings: Settings | None = None,
    requested_sources: list[str] | None = None,
) -> dict[str, SourceConnector]:
    """
    Retrieve only enabled and requested source connectors.
    If requested_sources is given, filter to those; otherwise return all enabled.
    """
    cfg = settings or get_settings()
    all_connectors = create_all_connectors(cfg)
    enabled: dict[str, SourceConnector] = {}

    for name, connector in all_connectors.items():
        if requested_sources is not None and name not in requested_sources:
            continue

        if connector.is_enabled(cfg):
            enabled[name] = connector
        else:
            logger.info("Connector '%s' is disabled by configuration", name)

    return enabled
