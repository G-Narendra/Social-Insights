"""
Multi-Target Global Coverage Ingestion Test.
Validates ingestion across brands, tech leaders, and famous people
using the newly expanded multi-connector suite (Wikipedia, LinkedIn Pulse, Hacker News, Google News, GitHub, etc.).
"""

import asyncio
import datetime
import sys

from app.db.session import init_db, get_session_factory
from app.services.keyword_service import get_or_create_keyword
from app.services.run_service import create_collection_run, get_run_by_id
from app.services.collection_job import execute_collection_pipeline


TARGETS = [
    {
        "keyword": "Elon Musk",
        "aliases": ["Musk"],
        "context_hint": "CEO of Tesla, SpaceX, xAI, neuralink",
        "type": "Famous Person / Tech Leader",
    },
    {
        "keyword": "NVIDIA",
        "aliases": ["NVDA", "GeForce"],
        "context_hint": "Semiconductor, GPU, AI chips company",
        "type": "Global Tech Brand",
    },
]


async def run_target_test(target: dict):
    term = target["keyword"]
    print(f"\n{'='*60}")
    print(f"Testing Ingestion for: {term} ({target['type']})")
    print(f"{'='*60}")

    factory = get_session_factory()
    async with factory() as session:
        kw = await get_or_create_keyword(
            session=session,
            term=term,
            aliases=target.get("aliases"),
            context_hint=target.get("context_hint"),
        )
        keyword_id = kw.id

        run = await create_collection_run(
            session=session,
            keyword_id=keyword_id,
            requested_limit=35,
        )
        run_id = run.id

    # Run collection with 35 limit across enabled connectors
    # (Hacker News, Google News, Wikipedia, LinkedIn Wire, GitHub)
    await execute_collection_pipeline(
        keyword_id=keyword_id,
        run_id=run_id,
        keyword_term=term,
        limit=35,
        sources=["googlenews", "hackernews", "wikipedia", "linkedin", "github"],
        aliases=target.get("aliases"),
        context_hint=target.get("context_hint"),
    )

    async with factory() as session:
        completed_run = await get_run_by_id(session, run_id)
        assert completed_run is not None
        status = completed_run.status
        per_source = completed_run.per_source or {}

    print(f"Run ID: {run_id} | Final Status: {status}")
    print(f"Per-Source Breakdown: {per_source}")
    assert status == "succeeded", f"Collection for {term} did not succeed (status={status})"
    print(f"[PASS] Successfully ingested & enriched {term} across {len(per_source)} active sources!")


async def main():
    print("Initializing Database...")
    await init_db()

    for target in TARGETS:
        await run_target_test(target)

    print("\n" + "="*60)
    print(">>> ALL MULTI-TARGET BRAND & PUBLIC FIGURE INGESTIONS SUCCEEDED! <<<")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
