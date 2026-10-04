"""
GATE 5 Verification Script:
Verifies FastAPI REST API against a live running server.
Executes:
1. Health & readiness checks (/health, /ready)
2. Trigger collection: POST /api/collect keyword="Toyota"
3. Poll run status: GET /api/runs/{id} until completion
4. Mentions query: GET /api/mentions?keyword=Toyota
5. Stats overview: GET /api/stats/overview?keyword=Toyota
6. Insights summary: GET /api/insights/summary?keyword=Toyota
"""

from __future__ import annotations

import asyncio
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"


async def main() -> None:
    print("=== GATE 5 SMOKE TEST: Testing Live REST API Endpoints ===")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Step 1: Check health & ready
        print("\n[Step 1] Checking /health and /ready...")
        h_res = await client.get("/health")
        assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
        print(f"  /health -> {h_res.status_code} {h_res.json()}")

        r_res = await client.get("/ready")
        assert r_res.status_code == 200, f"Readiness check failed: {r_res.text}"
        print(f"  /ready  -> {r_res.status_code} {r_res.json()}")

        # Step 2: Trigger collection
        print("\n[Step 2] Triggering POST /api/collect (keyword='Toyota', limit=20)...")
        c_res = await client.post("/api/collect", json={"keyword": "Toyota", "limit": 20})
        assert c_res.status_code == 202, f"Trigger failed: {c_res.text}"
        c_data = c_res.json()
        run_id = c_data["run_id"]
        print(f"  Collection triggered successfully: run_id={run_id}, status={c_data['status']}")

        # Step 3: Poll run status until completion
        print(f"\n[Step 3] Polling /api/runs/{run_id} until completed...")
        max_polls = 30
        status = "queued"
        run_data = {}
        for poll_idx in range(1, max_polls + 1):
            await asyncio.sleep(2.0)
            p_res = await client.get(f"/api/runs/{run_id}")
            assert p_res.status_code == 200, f"Poll failed: {p_res.text}"
            run_data = p_res.json()
            status = run_data["status"]
            print(f"  Poll {poll_idx}/{max_polls}: status={status}")
            if status in ("succeeded", "completed", "failed"):
                break

        assert status in ("succeeded", "completed"), f"Run failed or timed out: {run_data}"
        print(f"  Run finished successfully! Status={status}")

        # Step 4: GET /api/mentions
        print("\n[Step 4] Querying GET /api/mentions?keyword=Toyota&limit=5...")
        m_res = await client.get("/api/mentions", params={"keyword": "Toyota", "limit": 5})
        assert m_res.status_code == 200, f"Mentions query failed: {m_res.text}"
        m_data = m_res.json()
        print(f"  Total matching mentions in DB: {m_data['total']}")
        print(f"  Returned page items: {len(m_data['items'])}")
        for idx, m in enumerate(m_data["items"][:2], 1):
            print(f"    Sample #{idx}: [{m['source'].upper()}] (sentiment={m['sentiment']}, topic={m['topic']}) {m['title'][:60]}...")

        # Step 5: GET /api/stats/overview
        print("\n[Step 5] Querying GET /api/stats/overview?keyword=Toyota...")
        s_res = await client.get("/api/stats/overview", params={"keyword": "Toyota"})
        assert s_res.status_code == 200, f"Stats overview failed: {s_res.text}"
        s_data = s_res.json()
        print(f"  Stats overview: total={s_data['total_mentions']}, sentiment={s_data['sentiment']}, top_topics={len(s_data['top_topics'])}, quality={s_data['quality']}")

        # Step 6: GET /api/insights/summary
        print("\n[Step 6] Querying GET /api/insights/summary?keyword=Toyota...")
        sum_res = await client.get("/api/insights/summary", params={"keyword": "Toyota"})
        assert sum_res.status_code == 200, f"Summary failed: {sum_res.text}"
        sum_data = sum_res.json()
        print(f"  Summary method: {sum_data['method']}")
        print(f"  Executive summary: {sum_data['content'][:120]}...")
        if sum_data.get("insights"):
            print(f"  Structured insights categories: {list(sum_data['insights'].keys())}")

        print("\n>>> ALL GATE 5 CHECKS PASSED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    asyncio.run(main())
