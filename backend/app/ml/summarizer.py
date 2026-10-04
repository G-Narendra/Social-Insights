"""
AI Summarizer and Insight Synthesizer.
Tier 2 (NVIDIA NIM) + Tier 3 (Deterministic Template Fallback) with
fingerprint-based result caching to prevent redundant API calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Keyword, Mention, Summary
from app.ml.llm_client import LLMClient
from app.schemas.insights import InsightItem, StructuredInsights, SummaryResponse
from app.schemas.stats import OverviewStatsResponse
from app.services.stats_service import get_overview_stats

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def compute_data_fingerprint(keyword: str, total: int, pos: int, neg: int, last_id: int) -> str:
    """Create a deterministic hash representing the exact state of underlying data."""
    raw = f"{keyword}:{total}:{pos}:{neg}:{last_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


async def get_or_generate_summary(
    session: AsyncSession,
    keyword_id: int,
    force_refresh: bool = False,
    llm_client: LLMClient | None = None,
) -> SummaryResponse:
    """
    Retrieve cached summary or generate a new one via LLM (Tier 2) or Template (Tier 3).
    """
    keyword = await session.get(Keyword, keyword_id)
    if not keyword:
        raise ValueError(f"Keyword ID {keyword_id} not found")

    stats = await get_overview_stats(session, keyword_id)
    if stats.total_mentions == 0:
        return SummaryResponse(
            id=0,
            keyword_id=keyword_id,
            keyword=keyword.term,
            content=f"No mentions collected yet for '{keyword.term}'. Click Collect to gather public social discussions.",
            method="template",
            model_name="none",
            prompt_version="v1",
            created_at=keyword.created_at,
            insights=StructuredInsights(),
        )

    # Get last mention ID for fingerprinting
    last_mention_query = (
        select(Mention.id)
        .where(Mention.keyword_id == keyword_id)
        .order_by(Mention.id.desc())
        .limit(1)
    )
    last_id_res = await session.execute(last_mention_query)
    last_id = last_id_res.scalar_one_or_none() or 0

    fingerprint = compute_data_fingerprint(
        keyword=keyword.term,
        total=stats.total_mentions,
        pos=stats.sentiment.positive,
        neg=stats.sentiment.negative,
        last_id=last_id,
    )

    # Check cache if not forcing refresh
    if not force_refresh:
        cache_query = (
            select(Summary)
            .where(Summary.keyword_id == keyword_id)
            .where(Summary.data_fingerprint == fingerprint)
            .order_by(Summary.created_at.desc())
            .limit(1)
        )
        cached = (await session.execute(cache_query)).scalar_one_or_none()
        if cached:
            insights_obj = None
            if cached.insights:
                try:
                    insights_obj = StructuredInsights.model_validate(cached.insights)
                except Exception:
                    insights_obj = None

            return SummaryResponse(
                id=cached.id,
                keyword_id=keyword_id,
                keyword=keyword.term,
                content=cached.content,
                method=cached.method,
                model_name=cached.model_name,
                prompt_version=cached.prompt_version,
                created_at=cached.created_at,
                insights=insights_obj,
            )

    # Gather representative samples (up to 3 positive, 3 negative, 3 neutral)
    sample_query = (
        select(Mention.id, Mention.text_clean, Mention.sentiment, Mention.topic)
        .where(Mention.keyword_id == keyword_id)
        .where(Mention.status == "done")
        .order_by(Mention.published_at.desc().nulls_last())
        .limit(12)
    )
    samples = (await session.execute(sample_query)).all()

    # Attempt Tier 2 LLM generation if available
    client = llm_client or LLMClient()
    content = None
    structured_insights = None
    method = "template"
    model_name = "template-engine"

    if client.is_available:
        try:
            content, structured_insights = await _generate_llm_summary(
                client=client,
                keyword=keyword.term,
                stats=stats,
                samples=samples,
            )
            method = "llm"
            model_name = client.model
        except Exception as exc:
            logger.warning("Tier 2 LLM generation failed: %s. Reverting to Tier 3 template.", exc)

    # Tier 3: Deterministic template fallback
    if not content:
        content = _generate_template_summary(keyword.term, stats, samples)
        structured_insights = _generate_template_insights(samples, stats)
        method = "template"
        model_name = "template-engine"

    # Persist summary record
    summary_row = Summary(
        keyword_id=keyword_id,
        data_fingerprint=fingerprint,
        method=method,
        model_name=model_name,
        prompt_version="v1",
        content=content,
        insights=structured_insights.model_dump() if structured_insights else None,
    )
    session.add(summary_row)
    await session.commit()
    await session.refresh(summary_row)

    return SummaryResponse(
        id=summary_row.id,
        keyword_id=keyword_id,
        keyword=keyword.term,
        content=content,
        method=method,
        model_name=model_name,
        prompt_version="v1",
        created_at=summary_row.created_at,
        insights=structured_insights,
    )


async def _generate_llm_summary(
    client: LLMClient,
    keyword: str,
    stats: OverviewStatsResponse,
    samples: list[Any],
) -> tuple[str, StructuredInsights]:
    """Generate summary and structured insights via NVIDIA NIM."""
    sys_prompt = (PROMPTS_DIR / "summary_v1.txt").read_text(encoding="utf-8")
    insights_sys_prompt = (PROMPTS_DIR / "insights_v1.txt").read_text(encoding="utf-8")

    # Format structured context
    user_context = f"""TARGET KEYWORD: {keyword}
AGGREGATE METRICS:
- Total Mentions: {stats.total_mentions}
- Sentiment: Positive={stats.sentiment.positive} ({stats.sentiment.positive_pct}%), Neutral={stats.sentiment.neutral} ({stats.sentiment.neutral_pct}%), Negative={stats.sentiment.negative} ({stats.sentiment.negative_pct}%)
- Top Topics: {', '.join([f'{t.topic} ({t.percentage}%)' for t in stats.top_topics[:4]])}

REPRESENTATIVE SAMPLES:
"""
    for mid, text, sent, top in samples:
        safe_text = (text or "")[:180].replace("<", "&lt;").replace(">", "&gt;")
        user_context += f'<mention id="{mid}" sentiment="{sent}" topic="{top}">{safe_text}</mention>\n'

    # 1. Generate text summary
    summary_prompt = user_context + "\nSynthesize a 3-5 sentence executive summary in paragraph form."
    response = await client._client.chat.completions.create(
        model=client.model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": summary_prompt},
        ],
        temperature=0.1,
        max_tokens=250,
    )
    summary_text = response.choices[0].message.content or ""

    # 2. Generate structured insights JSON
    insights_json = await client.generate_json(
        system_prompt=insights_sys_prompt,
        user_prompt=user_context + "\nExtract emerging complaints, requested features, pain points, positive themes, and opportunities.",
    )

    insights_obj = StructuredInsights()
    if insights_json:
        try:
            insights_obj = StructuredInsights.model_validate(insights_json)
        except Exception:
            insights_obj = _generate_template_insights(samples, stats)

    return summary_text.strip(), insights_obj


def _generate_template_summary(
    keyword: str,
    stats: OverviewStatsResponse,
    samples: list[Any],
) -> str:
    """
    Tier 3 deterministic executive summary synthesis.
    Builds factual, readable sentences from aggregates without hallucinations.
    """
    total = stats.total_mentions
    pos_pct = stats.sentiment.positive_pct
    neg_pct = stats.sentiment.negative_pct
    neu_pct = stats.sentiment.neutral_pct

    # Determine dominant sentiment
    if pos_pct >= 45.0:
        dominant = "predominantly positive"
        tone_clause = f"Consumers express high satisfaction, accounting for {pos_pct}% of total sentiment."
    elif neg_pct >= 40.0:
        dominant = "predominantly critical"
        tone_clause = f"Negative sentiment dominates discussion at {neg_pct}%, indicating elevated consumer frustration."
    else:
        dominant = "balanced and neutral"
        tone_clause = f"Public sentiment is steady with {neu_pct}% neutral, {pos_pct}% positive, and {neg_pct}% negative mentions."

    top_topics_str = ""
    if stats.top_topics:
        t1 = stats.top_topics[0]
        top_topics_str = f"The primary driver of discussion is {t1.topic.replace('_', ' ')} ({t1.percentage}% of mentions)"
        if len(stats.top_topics) > 1:
            t2 = stats.top_topics[1]
            top_topics_str += f", followed by {t2.topic.replace('_', ' ')} ({t2.percentage}%)"
        top_topics_str += "."

    source_names = ", ".join([f"{src} ({cnt})" for src, cnt in list(stats.sources.items())[:3]])

    summary_paragraphs = [
        f"Public discussion regarding {keyword} across {total} analyzed mentions is {dominant}. {tone_clause}",
        f"{top_topics_str} Ingestion gathered data across multiple web channels including {source_names}.",
        f"Data quality filtering screened out {stats.quality.total_dropped} irrelevant, duplicate, or spam records, retaining {stats.quality.total_kept} qualified mentions for high-confidence intelligence.",
    ]

    return " ".join(summary_paragraphs)


def _generate_template_insights(
    samples: list[Any],
    stats: OverviewStatsResponse,
) -> StructuredInsights:
    """Extract structured insights from samples and topic distributions deterministically."""
    feature_patterns = re.compile(r"\b(wish|should add|would love|missing|needs|hope)\b", re.IGNORECASE)

    emerging_complaints = []
    requested_features = []
    pain_points = []
    positive_themes = []
    opportunities = []

    for mid, text, sent, top in samples:
        t = text or ""
        # Requested features
        if feature_patterns.search(t):
            requested_features.append(
                InsightItem(
                    title="User Requested Enhancement",
                    description=t[:120] + "...",
                    evidence_mention_ids=[mid],
                    volume=1,
                    sentiment=sent,
                )
            )

        # Pain points
        if sent == "negative":
            pain_points.append(
                InsightItem(
                    title=f"Critical Issue in {top.title() if top else 'Quality'}",
                    description=t[:120] + "...",
                    evidence_mention_ids=[mid],
                    volume=1,
                    sentiment="negative",
                )
            )

        # Positive themes
        if sent == "positive":
            positive_themes.append(
                InsightItem(
                    title=f"Strength in {top.title() if top else 'Product'}",
                    description=t[:120] + "...",
                    evidence_mention_ids=[mid],
                    volume=1,
                    sentiment="positive",
                )
            )

    # Opportunities derived from pain points
    if pain_points:
        opportunities.append(
            InsightItem(
                title="Service Quality Differentiation",
                description=f"Addressing top complaints in {stats.top_topics[0].topic if stats.top_topics else 'pricing'} offers immediate brand perception uplift.",
                evidence_mention_ids=[p.evidence_mention_ids[0] for p in pain_points[:2] if p.evidence_mention_ids],
                volume=len(pain_points),
            )
        )

    return StructuredInsights(
        emerging_complaints=pain_points[:3],
        requested_features=requested_features[:3],
        pain_points=pain_points[:3],
        positive_themes=positive_themes[:3],
        opportunities=opportunities[:2],
    )
