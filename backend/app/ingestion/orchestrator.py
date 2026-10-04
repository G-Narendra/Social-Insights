"""
Ingestion Orchestrator.
Runs source connectors concurrently with fault isolation, timeout limits,
and per-source telemetry tracking.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any

from app.config import Settings, get_settings
from app.ingestion.base import SourceConnector
from app.ingestion.registry import get_enabled_connectors
from app.schemas.mentions import RawMention

logger = logging.getLogger(__name__)


class IngestionResult:
    """Aggregated output from a multi-source collection run."""

    def __init__(self) -> None:
        self.mentions: list[RawMention] = []
        self.per_source: dict[str, int] = {}
        self.errors: list[dict[str, Any]] = []
        self.status: str = "succeeded"  # succeeded, partial, failed


async def _run_single_source(
    connector: SourceConnector,
    keyword: str,
    since: datetime.datetime | None,
    limit: int,
    timeout_seconds: float = 20.0,
) -> tuple[str, list[RawMention], str | None]:
    """
    Execute collection for one source with strict timeout and exception isolation.
    """
    name = connector.name
    results: list[RawMention] = []

    try:
        async with asyncio.timeout(timeout_seconds):
            async for mention in connector.search(keyword=keyword, since=since, limit=limit):
                results.append(mention)
        return name, results, None
    except TimeoutError:
        error_msg = f"Timed out after {timeout_seconds}s"
        logger.warning("[%s] Collection timed out for '%s'", name, keyword)
        return name, results, error_msg
    except Exception as exc:
        error_msg = str(exc)
        logger.exception("[%s] Unexpected failure during collection: %s", name, exc)
        return name, results, error_msg


async def run_ingestion(
    keyword: str,
    sources: list[str] | None = None,
    since: datetime.datetime | None = None,
    limit: int = 100,
    settings: Settings | None = None,
) -> IngestionResult:
    """
    Run all enabled connectors concurrently.
    Guarantees that a failure in one connector never aborts the overall run.
    """
    cfg = settings or get_settings()
    enabled_connectors = get_enabled_connectors(cfg, requested_sources=sources)
    result = IngestionResult()

    if not enabled_connectors:
        logger.warning("No connectors enabled for keyword '%s'", keyword)
        result.status = "failed"
        result.errors.append({"error": "No connectors enabled or available"})
        return result

    # Divide requested limit fairly across enabled connectors with a minimum of 20
    per_source_limit = max(limit // len(enabled_connectors), 25)

    tasks = [
        _run_single_source(
            connector=conn,
            keyword=keyword,
            since=since,
            limit=per_source_limit,
        )
        for conn in enabled_connectors.values()
    ]

    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    for item in task_results:
        if isinstance(item, Exception):
            logger.error("Gather exception in ingestion: %s", item)
            result.errors.append({"error": str(item)})
            continue

        name, mentions, error = item
        result.mentions.extend(mentions)
        result.per_source[name] = len(mentions)

        if error:
            result.errors.append(
                {
                    "source": name,
                    "error": error,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                }
            )

    # Determine final aggregate status
    total_sources = len(enabled_connectors)
    failed_sources = len(result.errors)

    if failed_sources == 0:
        result.status = "succeeded"
    elif failed_sources < total_sources:
        result.status = "partial"
    else:
        result.status = "failed"

    logger.info(
        "Ingestion completed for '%s': status=%s, total=%d, sources=%s",
        keyword,
        result.status,
        len(result.mentions),
        result.per_source,
    )
    return result
