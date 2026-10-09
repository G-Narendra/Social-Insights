"""
Full background collection pipeline coordinator.
Executes multi-source ingestion, processing pipeline, Tier 1 ML enrichment,
and alert evaluations in an asynchronous worker task.
"""

from __future__ import annotations

import asyncio
import datetime
import logging

from app.db.session import get_session_factory
from app.ingestion.orchestrator import run_ingestion
from app.ml.alerts import evaluate_sentiment_spike_alerts
from app.ml.sentiment import analyze_sentiment_batch
from app.ml.topics import classify_topics_batch
from app.processing.pipeline import process_raw_mentions
from app.services.keyword_service import update_last_collected
from app.services.mention_service import (
    bulk_update_mention_enrichments,
)
from app.services.run_service import update_run_status

logger = logging.getLogger(__name__)


async def execute_collection_pipeline(
    keyword_id: int,
    run_id: int,
    keyword_term: str,
    sources: list[str] | None = None,
    limit: int = 100,
    aliases: list[str] | None = None,
    context_hint: str | None = None,
) -> None:
    """
    Run full end-to-end collection, processing, and enrichment pipeline in background.
    """
    factory = get_session_factory()

    # Mark run as running
    async with factory() as session:
        await update_run_status(session, run_id=run_id, status="running")

    try:
        # Stage 1: Multi-source Ingestion
        logger.info("[Run %d] Ingesting mentions for '%s'...", run_id, keyword_term)
        ingestion_result = await run_ingestion(
            keyword=keyword_term,
            sources=sources,
            limit=limit,
        )

        # Stage 2: Data Processing Pipeline
        logger.info(
            "[Run %d] Processing %d ingested raw mentions...",
            run_id,
            len(ingestion_result.mentions),
        )
        async with factory() as session:
            kept_mentions, pipeline_stats = await process_raw_mentions(
                session=session,
                keyword_id=keyword_id,
                run_id=run_id,
                keyword=keyword_term,
                raw_mentions=ingestion_result.mentions,
                aliases=aliases,
                context_hint=context_hint,
            )

        # Stage 3: Tier 1 ML Enrichment (Sentiment + Topics)
        if kept_mentions:
            logger.info(
                "[Run %d] Running ML enrichment on %d mentions in worker thread...",
                run_id,
                len(kept_mentions),
            )
            texts = [m.text_clean or m.text_raw for m in kept_mentions]

            # Offload heavy CPU inference to worker thread so asyncio event loop remains 100% responsive
            sent_preds = await asyncio.to_thread(analyze_sentiment_batch, texts, batch_size=32)
            topic_preds = await asyncio.to_thread(classify_topics_batch, texts)

            # Persist predictions to database in a single atomic transaction
            enrichment_payloads = []
            for i, mention in enumerate(kept_mentions):
                sp = sent_preds[i] if i < len(sent_preds) else None
                tp = topic_preds[i] if i < len(topic_preds) else None

                enrichment_payloads.append(
                    {
                        "mention_id": mention.id,
                        "sentiment": sp.label if sp else "neutral",
                        "sentiment_score": sp.score if sp else 0.5,
                        "topic": tp.topic if tp else "other",
                        "topic_score": tp.score if tp else 0.5,
                        "secondary_topic": tp.secondary_topic if tp else None,
                        "enriched_by": "model",
                        "embedding": tp.embedding if tp else None,
                    }
                )

            async with factory() as session:
                await bulk_update_mention_enrichments(session, enrichment_payloads)

        # Stage 4: Alert Evaluations (Sentiment Spikes)
        async with factory() as session:
            await evaluate_sentiment_spike_alerts(
                session=session,
                keyword_id=keyword_id,
                keyword_term=keyword_term,
            )
            # Update last collected timestamp
            await update_last_collected(session, keyword_id=keyword_id)

            # Stage 5: Finalize Run Status
            final_status = ingestion_result.status
            await update_run_status(
                session=session,
                run_id=run_id,
                status=final_status,
                per_source=ingestion_result.per_source,
                errors=ingestion_result.errors,
            )

        logger.info(
            "[Run %d] Successfully completed for '%s' with status: %s",
            run_id,
            keyword_term,
            final_status,
        )

    except Exception as exc:
        logger.exception("[Run %d] Fatal error during collection run: %s", run_id, exc)
        async with factory() as session:
            await update_run_status(
                session=session,
                run_id=run_id,
                status="failed",
                errors=[
                    {
                        "error": str(exc),
                        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                    }
                ],
            )
