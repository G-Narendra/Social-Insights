"""
Processing Pipeline Orchestrator.
Coordinates normalization, canonicalization, deduplication, relevance verification,
and quality filtering in an auditable, idempotent pipeline.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mention
from app.processing.canonical_url import canonicalize_url
from app.processing.dedup import Deduplicator, compute_content_hash
from app.processing.normalize import normalize_text
from app.processing.quality import check_quality
from app.processing.relevance import check_relevance
from app.schemas.mentions import RawMention
from app.services.mention_service import upsert_mention

logger = logging.getLogger(__name__)


class PipelineStats:
    """Telemetry and drop statistics for a pipeline run."""

    def __init__(self) -> None:
        self.total_processed: int = 0
        self.total_kept: int = 0
        self.total_dropped: int = 0
        self.drop_reasons: dict[str, int] = {}

    def record_drop(self, reason: str) -> None:
        self.total_processed += 1
        self.total_dropped += 1
        self.drop_reasons[reason] = self.drop_reasons.get(reason, 0) + 1

    def record_kept(self) -> None:
        self.total_processed += 1
        self.total_kept += 1


async def process_raw_mentions(
    session: AsyncSession,
    keyword_id: int,
    run_id: int,
    keyword: str,
    raw_mentions: list[RawMention],
    aliases: list[str] | None = None,
    context_hint: str | None = None,
) -> tuple[list[Mention], PipelineStats]:
    """
    Execute full processing pipeline over ingested mentions:
    1. Normalization & Canonicalization
    2. Exact & Near Deduplication
    3. Relevance Filtering
    4. Quality & Spam Pruning
    5. Persistence to Database
    Returns (kept_mentions, pipeline_stats).
    """
    stats = PipelineStats()
    deduplicator = Deduplicator(near_dedup_threshold=0.85)
    kept_mentions: list[Mention] = []

    for raw in raw_mentions:
        # Step 1: Canonicalize URL
        canonical_url = canonicalize_url(raw.url)

        # Step 2: Normalize text
        text_clean = normalize_text(raw.text)
        content_hash = compute_content_hash(text_clean)

        # Upsert record in database with raw text intact
        mention, is_new = await upsert_mention(
            session=session,
            keyword_id=keyword_id,
            run_id=run_id,
            raw=raw,
            content_hash=content_hash,
            canonical_url=canonical_url,
        )

        mention.text_clean = text_clean

        # Step 3: Deduplication check
        is_dup, dup_reason = deduplicator.check_duplicate(
            content_hash=content_hash,
            canonical_url=canonical_url,
            text=text_clean,
            mention_id=str(mention.id),
        )
        if is_dup:
            mention.status = "dropped"
            mention.drop_reason = dup_reason
            stats.record_drop(dup_reason or "duplicate")
            continue

        # Step 4: Relevance check
        is_rel, rel_reason = check_relevance(
            text=text_clean,
            title=raw.title,
            keyword=keyword,
            aliases=aliases,
            context_hint=context_hint,
        )
        if not is_rel:
            mention.status = "dropped"
            mention.drop_reason = rel_reason
            stats.record_drop(rel_reason or "irrelevant")
            continue

        # Step 5: Quality & spam check
        is_qual, qual_reason, detected_lang = check_quality(text=text_clean)
        mention.language = detected_lang
        if not is_qual:
            mention.status = "dropped"
            mention.drop_reason = qual_reason
            stats.record_drop(qual_reason or "quality_failed")
            continue

        # Passes all quality and relevance gates
        mention.status = "relevant"
        mention.drop_reason = None
        stats.record_kept()
        kept_mentions.append(mention)

    await session.commit()
    logger.info(
        "Pipeline finished: total=%d, kept=%d, dropped=%d, reasons=%s",
        stats.total_processed,
        stats.total_kept,
        stats.total_dropped,
        stats.drop_reasons,
    )
    return kept_mentions, stats
