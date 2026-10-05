"""
End-to-End Comprehensive Platform Validation Suite
Tests all 4 dashboard views, data flows, filters, API endpoints, and system contracts.
"""

import sys
import time
import httpx

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://127.0.0.1:8000"


def log_test(step: str, success: bool, detail: str = ""):
    status_icon = "PASS" if success else "FAIL"
    print(f"[{status_icon}] {step:<45} {detail}")
    if not success:
        sys.exit(1)


def main():
    print("=" * 70)
    print("   SOCIAL INSIGHTS — FULL END-TO-END SYSTEM VALIDATION SUITE")
    print("=" * 70)

    client = httpx.Client(timeout=15.0)

    # 1. Frontend Web Server
    try:
        res = client.get(FRONTEND_URL)
        log_test(
            "1. Next.js Frontend Server",
            res.status_code == 200 and "Social Insights" in res.text,
            f"Status {res.status_code}, HTML Title Verified",
        )
    except Exception as e:
        log_test("1. Next.js Frontend Server", False, str(e))

    # 2. Backend Health & Readiness
    try:
        res = client.get(f"{BACKEND_URL}/health")
        log_test(
            "2. Backend Health Check (/health)",
            res.status_code == 200 and res.json().get("status") == "ok",
            f"Status {res.status_code}, DB Health OK",
        )
        res_ready = client.get(f"{BACKEND_URL}/ready")
        log_test(
            "3. Backend Readiness Check (/ready)",
            res_ready.status_code == 200 and res_ready.json().get("status") == "ready",
            "Models & Storage Initialized",
        )
    except Exception as e:
        log_test("2/3. Backend Health/Ready", False, str(e))

    # 3. Tracked Keywords
    keyword = "Toyota"
    try:
        res = client.get(f"{FRONTEND_URL}/api/keywords")
        data = res.json()
        has_toyota = any(k.get("term") == keyword for k in data)
        log_test(
            "4. Tracked Keywords Query (/api/keywords)",
            res.status_code == 200 and has_toyota,
            f"Found {len(data)} keywords, default '{keyword}' present",
        )
    except Exception as e:
        log_test("4. Tracked Keywords Query", False, str(e))

    # 4. Overview Tab — Statistics
    try:
        res = client.get(f"{FRONTEND_URL}/api/stats/overview", params={"keyword": keyword})
        data = res.json()
        total = data.get("total_mentions", 0)
        net_score = data.get("sentiment", {}).get("net_score", 0)
        log_test(
            "5. Overview Tab: KPI Stats (/api/stats/overview)",
            res.status_code == 200 and total > 0,
            f"Total Mentions: {total}, Net Score: {net_score:.2f}",
        )
    except Exception as e:
        log_test("5. Overview Tab Stats", False, str(e))

    # 5. Overview Tab — Time Series
    try:
        res = client.get(
            f"{FRONTEND_URL}/api/stats/timeseries", params={"keyword": keyword, "interval": "day"}
        )
        data = res.json()
        buckets = data.get("buckets", []) or data.get("points", [])
        log_test(
            "6. Overview Tab: Time Series (/api/stats/timeseries)",
            res.status_code == 200 and len(buckets) > 0,
            f"Loaded {len(buckets)} daily volume data points",
        )
    except Exception as e:
        log_test("6. Overview Tab Time Series", False, str(e))

    # 6. Trends & Topic Velocity (BON-01)
    try:
        res = client.get(
            f"{FRONTEND_URL}/api/insights/trends", params={"keyword": keyword, "window_days": 7}
        )
        data = res.json()
        trends = data.get("trends", [])
        log_test(
            "7. Topic Velocity & Trends (/api/insights/trends)",
            res.status_code == 200,
            f"Trend items detected: {len(trends)}",
        )
    except Exception as e:
        log_test("7. Topic Velocity & Trends", False, str(e))

    # 7. Anomaly Alerts (BON-04)
    try:
        res = client.get(f"{FRONTEND_URL}/api/alerts", params={"keyword": keyword})
        data = res.json()
        alerts = data if isinstance(data, list) else data.get("alerts", [])
        log_test(
            "8. Negative Spike Alerts (/api/alerts)",
            res.status_code == 200,
            f"Anomaly alerts active: {len(alerts)}",
        )
    except Exception as e:
        log_test("8. Negative Spike Alerts", False, str(e))

    # 8. Mentions Feed — Filtering & Pagination
    try:
        # Standard first page
        res = client.get(
            f"{FRONTEND_URL}/api/mentions", params={"keyword": keyword, "page": 1, "limit": 15}
        )
        data = res.json()
        mentions = data.get("items", [])
        total_items = data.get("total", 0)
        log_test(
            "9. Mentions Feed: Page 1 (/api/mentions)",
            res.status_code == 200 and len(mentions) > 0,
            f"Returned {len(mentions)} items (Total: {total_items})",
        )

        # Sentiment Filter: Negative
        res_neg = client.get(
            f"{FRONTEND_URL}/api/mentions",
            params={"keyword": keyword, "sentiment": "negative", "page": 1, "limit": 5},
        )
        neg_items = res_neg.json().get("items", [])
        all_neg = all(m.get("sentiment") == "negative" for m in neg_items)
        log_test(
            "10. Mentions Feed: Sentiment Filter (negative)",
            res_neg.status_code == 200 and all_neg,
            f"Filtered {len(neg_items)} strictly negative mentions",
        )

        # Source Filter: Reddit or Hacker News
        res_src = client.get(
            f"{FRONTEND_URL}/api/mentions",
            params={"keyword": keyword, "source": "hacker_news", "page": 1, "limit": 5},
        )
        src_items = res_src.json().get("items", [])
        all_src = all(m.get("source") == "hacker_news" for m in src_items)
        log_test(
            "11. Mentions Feed: Source Filter (hacker_news)",
            res_src.status_code == 200 and (len(src_items) == 0 or all_src),
            f"Filtered {len(src_items)} hacker_news mentions",
        )
    except Exception as e:
        log_test("9-11. Mentions Feed Validation", False, str(e))

    # 9. AI Summary & Structured Product Intelligence
    try:
        res = client.get(f"{FRONTEND_URL}/api/insights/summary", params={"keyword": keyword})
        data = res.json()
        content = data.get("content", "")
        method = data.get("method", "")
        model = data.get("model_name", "")
        log_test(
            "12. AI Insights Tab: Summary (/api/insights/summary)",
            res.status_code == 200 and len(content) > 20,
            f"Method: {method}, Model: {model} ({len(content)} chars)",
        )
    except Exception as e:
        log_test("12. AI Insights Summary", False, str(e))

    # 10. Competitor Benchmark (BON-02)
    try:
        brands = ["Toyota", "Honda", "Tesla"]
        res = client.get(f"{FRONTEND_URL}/api/compare", params={"keywords": ",".join(brands)})
        data = res.json()
        comps = data.get("competitors", [])
        log_test(
            "13. Compare Tab: Multi-Brand Matrix (/api/compare)",
            res.status_code == 200 and len(comps) == 3,
            f"Compared brands: {', '.join([c.get('keyword', '') for c in comps])}",
        )
    except Exception as e:
        log_test("13. Competitor Comparison", False, str(e))

    # 11. End-to-End Latency Benchmark
    try:
        t0 = time.time()
        client.get(f"{FRONTEND_URL}/api/stats/overview", params={"keyword": keyword})
        t_overview = (time.time() - t0) * 1000

        t0 = time.time()
        client.get(f"{FRONTEND_URL}/api/mentions", params={"keyword": keyword, "limit": 15})
        t_mentions = (time.time() - t0) * 1000

        log_test(
            "14. Performance & Response Latency",
            t_overview < 200 and t_mentions < 200,
            f"Overview: {t_overview:.1f}ms | Mentions: {t_mentions:.1f}ms (<200ms target)",
        )
    except Exception as e:
        log_test("14. Latency Benchmark", False, str(e))

    print("=" * 70)
    print(">>> ALL 14 END-TO-END VALIDATION GATES PASSED WITH ZERO ERRORS! <<<")
    print("=" * 70)


if __name__ == "__main__":
    main()
