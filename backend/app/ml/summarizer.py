"""
AI Summarizer and Insight Synthesizer.
Tier 2 (NVIDIA NIM) + Tier 3 (Deterministic Template Fallback) with
fingerprint-based result caching to prevent redundant API calls.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from sqlalchemy import select
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


def _clean_snippet(title: str | None, text: str | None, max_len: int = 240) -> str:
    """Clean HTML tags, raw URLs, and truncate gracefully at complete thoughts."""
    raw = (title + ". " if title and title != text else "") + (text or "")
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    # Remove raw URLs
    cleaned = re.sub(r"https?://\S+", "", cleaned)
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    if len(cleaned) <= max_len:
        return cleaned
    trimmed = cleaned[:max_len]
    last_stop = max(trimmed.rfind(". "), trimmed.rfind("! "), trimmed.rfind("? "))
    if last_stop > max_len // 2:
        return trimmed[: last_stop + 1]
    last_space = trimmed.rfind(" ")
    if last_space > 0:
        return trimmed[:last_space] + "..."
    return trimmed + "..."


async def _fetch_representative_samples(
    session: AsyncSession, keyword_id: int
) -> list[tuple[int, str, str | None, str | None, str | None]]:
    """Fetch representative mentions across positive, negative, key topics, and recent mentions."""
    samples_map: dict[int, tuple[int, str, str | None, str | None, str | None]] = {}

    # 1. Fetch positive samples
    q_pos = (
        select(Mention.id, Mention.title, Mention.text_clean, Mention.sentiment, Mention.topic)
        .where(
            Mention.keyword_id == keyword_id,
            Mention.status == "done",
            Mention.sentiment == "positive",
        )
        .order_by(Mention.id.desc())
        .limit(5)
    )
    for row in (await session.execute(q_pos)).all():
        samples_map[row[0]] = (row[0], row[1] or "", row[2] or "", row[3], row[4])

    # 2. Fetch negative samples
    q_neg = (
        select(Mention.id, Mention.title, Mention.text_clean, Mention.sentiment, Mention.topic)
        .where(
            Mention.keyword_id == keyword_id,
            Mention.status == "done",
            Mention.sentiment == "negative",
        )
        .order_by(Mention.id.desc())
        .limit(5)
    )
    for row in (await session.execute(q_neg)).all():
        samples_map[row[0]] = (row[0], row[1] or "", row[2] or "", row[3], row[4])

    # 3. Fetch feature and quality topic samples
    q_topics = (
        select(Mention.id, Mention.title, Mention.text_clean, Mention.sentiment, Mention.topic)
        .where(
            Mention.keyword_id == keyword_id,
            Mention.status == "done",
            Mention.topic.in_(["features", "quality", "product", "complaints"]),
        )
        .order_by(Mention.id.desc())
        .limit(6)
    )
    for row in (await session.execute(q_topics)).all():
        samples_map[row[0]] = (row[0], row[1] or "", row[2] or "", row[3], row[4])

    # 4. Fill with recent mentions up to 16
    if len(samples_map) < 16:
        q_recent = (
            select(Mention.id, Mention.title, Mention.text_clean, Mention.sentiment, Mention.topic)
            .where(Mention.keyword_id == keyword_id, Mention.status == "done")
            .order_by(Mention.published_at.desc().nulls_last(), Mention.id.desc())
            .limit(16)
        )
        for row in (await session.execute(q_recent)).all():
            if row[0] not in samples_map:
                samples_map[row[0]] = (row[0], row[1] or "", row[2] or "", row[3], row[4])

    return list(samples_map.values())


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

    # Gather representative samples across sentiments & key topics
    samples = await _fetch_representative_samples(session, keyword_id)

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
        structured_insights = _generate_template_insights(samples, stats, keyword=keyword.term)
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
    for item in samples:
        if len(item) == 5:
            mid, title, text, sent, top = item
        else:
            mid, text, sent, top = item
            title = ""
        safe_text = (
            _clean_snippet(title, text, max_len=180).replace("<", "&lt;").replace(">", "&gt;")
        )
        user_context += (
            f'<mention id="{mid}" sentiment="{sent}" topic="{top}">{safe_text}</mention>\n'
        )

    # 1. Generate text summary
    summary_prompt = (
        user_context + "\nSynthesize a 3-5 sentence executive summary in paragraph form."
    )
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
        user_prompt=user_context
        + "\nExtract emerging complaints, requested features, pain points, positive themes, and opportunities.",
    )

    insights_obj = StructuredInsights()
    if insights_json:
        try:
            insights_obj = StructuredInsights.model_validate(insights_json)
        except Exception:
            insights_obj = _generate_template_insights(samples, stats, keyword=keyword)

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
        tone_clause = (
            f"Consumers express high satisfaction, accounting for {pos_pct}% of total sentiment."
        )
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
    keyword: str = "",
) -> StructuredInsights:
    """Extract structured insights from samples and topic distributions deterministically."""
    feature_patterns = re.compile(
        r"\b(wish|should add|would love|missing|needs|hope|feature|support|integrate|api|release|upgrade)\b",
        re.IGNORECASE,
    )

    emerging_complaints: list[InsightItem] = []
    requested_features: list[InsightItem] = []
    pain_points: list[InsightItem] = []
    positive_themes: list[InsightItem] = []
    opportunities: list[InsightItem] = []

    for item in samples:
        if len(item) == 5:
            mid, title, text, sent, top = item
        else:
            mid, text, sent, top = item
            title = ""

        snippet = _clean_snippet(title, text, max_len=240)
        if not snippet or len(snippet) < 15:
            continue

        topic_label = (top or "Product").replace("_", " ").title()

        # Requested features: matches pattern or classified under features
        if top == "features" or feature_patterns.search(snippet):
            if len(requested_features) < 3:
                requested_features.append(
                    InsightItem(
                        title=f"Feature Focus: {topic_label}",
                        description=snippet,
                        evidence_mention_ids=[mid],
                        volume=1,
                        sentiment=sent or "neutral",
                    )
                )

        # Pain points and emerging complaints
        if sent == "negative" or top in ["complaints", "customer_service"]:
            p_item = InsightItem(
                title=f"User Friction in {topic_label}",
                description=snippet,
                evidence_mention_ids=[mid],
                volume=1,
                sentiment="negative",
            )
            if len(pain_points) < 3:
                pain_points.append(p_item)
            if (sent == "negative" or top == "complaints") and len(emerging_complaints) < 3:
                emerging_complaints.append(p_item)

        # Positive themes
        if sent == "positive" or top in ["quality", "product"]:
            if len(positive_themes) < 3:
                positive_themes.append(
                    InsightItem(
                        title=f"Positive Perception in {topic_label}",
                        description=snippet,
                        evidence_mention_ids=[mid],
                        volume=1,
                        sentiment="positive",
                    )
                )

    # Fallbacks if sample count was small
    if not requested_features and stats.top_topics:
        top_topic = stats.top_topics[0].topic.replace("_", " ").title()
        requested_features.append(
            InsightItem(
                title=f"Core Capability Interest: {top_topic}",
                description=f"Public attention centers heavily on {top_topic.lower()} with {stats.top_topics[0].percentage}% of volume. Users expect active updates and reliability here.",
                evidence_mention_ids=[],
                volume=stats.top_topics[0].count,
            )
        )

    if not positive_themes and stats.sentiment.positive > 0:
        positive_themes.append(
            InsightItem(
                title="Brand Advocacy & Reception",
                description=f"{stats.sentiment.positive} mentions reflect favorable community sentiment ({stats.sentiment.positive_pct}% positive share).",
                evidence_mention_ids=[],
                volume=stats.sentiment.positive,
                sentiment="positive",
            )
        )

    # Strategic Opportunities computed from aggregate metrics
    kw_name = keyword or stats.keyword
    if stats.top_topics:
        lead_t = stats.top_topics[0]
        t_name = lead_t.topic.replace("_", " ").title()
        opportunities.append(
            InsightItem(
                title=f"Capitalize on {t_name} Discussion Volume",
                description=f"{t_name} is the primary discussion driver ({lead_t.percentage}% of all mentions for {kw_name}). Publishing guides, customer stories, and feature deep-dives will maximize reach.",
                evidence_mention_ids=[],
                volume=lead_t.count,
            )
        )

    if stats.sentiment.neutral_pct >= 50.0:
        opportunities.append(
            InsightItem(
                title="Convert Neutral Mindshare into Advocates",
                description=f"{stats.sentiment.neutral_pct}% of mentions are neutral or informative. Targeted community engagement and transparent milestone updates can turn passive observers into active brand champions.",
                evidence_mention_ids=[],
                volume=stats.sentiment.neutral,
            )
        )
    elif stats.sentiment.negative_pct > 15.0:
        opportunities.append(
            InsightItem(
                title="Proactive Issue Resolution & Mitigation",
                description=f"Negative sentiment accounts for {stats.sentiment.negative_pct}% of discussions. Addressing recurring friction points will significantly elevate the Brand Reputation Health score.",
                evidence_mention_ids=[],
                volume=stats.sentiment.negative,
            )
        )
    else:
        opportunities.append(
            InsightItem(
                title="Amplify Positive User Endorsements",
                description=f"Strong positive sentiment ({stats.sentiment.positive_pct}%) provides valuable social proof. Repurpose community praise into marketing collateral and social campaigns.",
                evidence_mention_ids=[],
                volume=stats.sentiment.positive,
            )
        )

    return StructuredInsights(
        emerging_complaints=emerging_complaints[:3],
        requested_features=requested_features[:3],
        pain_points=pain_points[:3],
        positive_themes=positive_themes[:3],
        opportunities=opportunities[:2],
    )
