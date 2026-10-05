"""
Competitor Comparison Engine (BON-02).
Compares volume, sentiment mix, topic distribution, and top complaint themes
side-by-side across up to 4 tracked keywords.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Mention
from app.schemas.insights import CompareResponse, CompetitorMetrics
from app.services.keyword_service import get_keyword_by_term
from app.services.stats_service import get_overview_stats


async def compare_keywords(
    session: AsyncSession,
    terms: list[str],
) -> CompareResponse:
    """
    Produce a side-by-side analytical comparison of multiple brands/keywords.
    """
    competitors: list[CompetitorMetrics] = []

    for raw_term in terms[:4]:
        term = raw_term.strip()
        if not term:
            continue

        kw = await get_keyword_by_term(session, term)
        if not kw:
            sentiment_dict = {
                "positive_pct": 0.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
            }
            competitors.append(
                CompetitorMetrics(
                    keyword=term,
                    total_mentions=0,
                    positive_pct=0.0,
                    neutral_pct=0.0,
                    negative_pct=0.0,
                    sentiment=sentiment_dict,
                    top_topics=[],
                    common_complaints=["No data collected yet. Trigger collection to analyze."],
                    top_complaint_themes=["No data collected yet. Trigger collection to analyze."],
                )
            )
            continue

        stats = await get_overview_stats(session, kw.id)

        # Retrieve top complaint snippets
        complaints_query = (
            select(Mention.text_clean)
            .where(Mention.keyword_id == kw.id)
            .where(Mention.sentiment == "negative")
            .where(Mention.status == "done")
            .order_by(Mention.id.desc())
            .limit(3)
        )
        complaint_rows = (await session.execute(complaints_query)).scalars().all()
        common_complaints = [(c[:100] + "..." if len(c) > 100 else c) for c in complaint_rows if c]

        if not common_complaints:
            common_complaints = ["No significant complaints recorded."]

        top_topics = [t.topic.replace("_", " ").title() for t in stats.top_topics[:3]]

        sentiment_dict = {
            "positive_pct": stats.sentiment.positive_pct,
            "neutral_pct": stats.sentiment.neutral_pct,
            "negative_pct": stats.sentiment.negative_pct,
        }

        competitors.append(
            CompetitorMetrics(
                keyword=kw.term,
                keyword_id=kw.id,
                total_mentions=stats.total_mentions,
                positive_pct=stats.sentiment.positive_pct,
                neutral_pct=stats.sentiment.neutral_pct,
                negative_pct=stats.sentiment.negative_pct,
                sentiment=sentiment_dict,
                top_topics=top_topics,
                common_complaints=common_complaints,
                top_complaint_themes=common_complaints,
            )
        )

    return CompareResponse(competitors=competitors)
