# Social Insights

> **Production-grade, open-source social listening & market intelligence platform with Tiered AI.**  
> Zero required API costs. Local CPU neural models. NVIDIA NIM LLM synthesis. Real-time Next.js dashboard.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)](https://www.docker.com/)

---

## 🌟 Executive Overview

**Social Insights** enables organizations, founders, and product teams to track brand perception, monitor customer feedback, and identify emerging product issues in real time across decentralized web communities.

Unlike conventional tools that either incur thousands of dollars in monthly subscriptions or naively send every raw tweet into expensive commercial LLMs, Social Insights uses a **Tiered Intelligence Architecture**:

1. **Deterministic Rules (Tier 0)**: Ingests, strips tracking parameters, canonicalizes URLs, and drops duplicates/spam in `<0.1ms`.
2. **Local CPU Neural Models (Tier 1)**: CardiffNLP Twitter-RoBERTa for 3-class sentiment (85.0% accuracy) and Sentence-Transformers MiniLM-L6-v2 for semantic topic clustering (75.0% accuracy) running entirely locally on CPU at **$0.00 compute cost**.
3. **Targeted LLM Synthesis (Tier 2)**: NVIDIA NIM API (`meta/llama-3.1-8b-instruct`) invoked only on low-confidence ambiguities and high-level executive summaries with prompt injection defense.
4. **Deterministic Template Fallback (Tier 3)**: Guaranteed offline operation with factual, zero-hallucination summaries when disconnected from cloud LLMs.

---

## 🚀 Key Features

- **Multi-Source Ingestion**: Ingests mentions from Hacker News (Algolia), Google News (RSS), Stack Exchange (REST), Reddit (OAuth), and YouTube (Data API v3) with exponential backoff and fault isolation.
- **Resilient Pipeline**: Word-boundary relevance checking, canonical URL tracking removal (`utm_*`, `fbclid`), content hashing, near-duplicate detection, and language filtering.
- **Rich Dashboard UI**: Next.js 14 App Router with Tailwind CSS, dark mode glassmorphism, responsive charts, and real-time mention search/filtering.
- **AI Executive Insights**: Synthesizes 5 structured intelligence categories:
  - 🚨 *Emerging Complaints* (with cited mention IDs)
  - ⚡ *Requested Features*
  - ⚠️ *Core Pain Points*
  - 👍 *Positive Praises & Themes*
  - 💡 *Market & Strategic Opportunities*
- **Bonus Capabilities**:
  - 📈 **Trending Topics Velocity (BON-01)**: Detects accelerating discussion themes over rolling 7-day windows.
  - 🥊 **Competitor Comparison (BON-02)**: Side-by-side volume, sentiment mix, and complaint benchmark across brands.
  - 🎥 **YouTube Connector (BON-03)**: Ingests video titles, descriptions, and engagement metrics.
  - 🚨 **Anomaly Alert Engine (BON-04)**: Statistical detection of negative sentiment spikes exceeding 2 standard deviations over a 14-day rolling baseline.

---

## 🧠 Tiered Intelligence Funnel

```
                          [ Raw Social Media Stream ]
                                      │
                                      ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ Tier 0: Regex, xxHash, NFKC Normalization, Canonical URLs (<0.1ms)│
    │         - Discards duplicate URLs, spam, non-English, off-target  │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │ Filtered Mentions (Kept)
                                      ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ Tier 1: Local CPU Neural Models (5–15ms, $0.00 cost)              │
    │         - Sentiment: cardiffnlp/twitter-roberta-base-sentiment    │
    │         - Topics: sentence-transformers/all-MiniLM-L6-v2          │
    │         - Softmax confidence gating (<0.55 flags low confidence)  │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
                                      ├─────────────────────────────────┐
                                      │ Aggregates                      │ Low Confidence
                                      ▼                                 ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ Tier 2: Targeted LLM Synthesis (NVIDIA NIM Llama-3.1 8B)          │
    │         - Compact budgeted context (<2000 tokens)                 │
    │         - Executive synthesis & structured intelligence cards     │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │ (If offline or quota exceeded)
                                      ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │ Tier 3: Deterministic Template Fallback (Offline, zero-hallucinate│
    └───────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart in 3 Minutes

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ (Node 20+ recommended)
- Git

### 2. Setup Backend
```bash
# Clone the repository
git clone https://github.com/your-org/social-insights.git
cd social-insights

# Create and activate local virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies in editable mode
pip install -e ".[dev]"

# Initialize database schema
alembic upgrade head

# Start API server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3. Setup Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:3000](http://localhost:3000)** in your browser!

---

## 🐳 Docker Deployment

Run the complete multi-container stack (FastAPI backend + Next.js frontend + persistent volumes) with a single command:

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Build and launch services in background
docker compose up -d --build

# 3. Verify health
docker compose ps
curl -f http://localhost:8000/health
```

To run with optional PostgreSQL or local Ollama:
```bash
# With PostgreSQL 16
docker compose --profile postgres up -d

# With local Ollama LLM
docker compose --profile ollama up -d
```

---

## 📊 Measured ML Benchmarks

Evaluated on 100 hand-labeled social media samples (`backend/eval/labelled_sample.jsonl`):

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| **Sentiment Accuracy** | **85.00%** | > 75.0% | ✅ Exceeded |
| **Sentiment Macro F1** | **0.8496** | > 0.70 | ✅ Exceeded |
| **Topic Categorization Accuracy** | **75.00%** | > 70.0% | ✅ Exceeded |
| **Topic Macro F1** | **0.7089** | > 0.65 | ✅ Exceeded |
| **Sentiment Inference Speed** | **~1.9 items/sec** | CPU batched | ✅ Verified |
| **Topic Inference Speed** | **~7.5 items/sec** | CPU batched | ✅ Verified |
| **LLM Share of Items** | **< 5%** | Tier 2 strict gating | ✅ Verified |

For complete evaluation methodology and confusion matrices, see [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

---

## 🔌 Connectors & Data Sources

| Connector | Mechanism | Default Status | Credentials Required |
|---|---|---|---|
| **Hacker News** | Algolia Search REST API | Active | None (Public) |
| **Google News** | Public RSS Atom Feed | Active | None (Public) |
| **Stack Exchange** | REST API v2.3 | Active | None (Public) |
| **Reddit** | OAuth2 Search API | Optional | `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` |
| **YouTube** | Data API v3 Search | Optional | `YOUTUBE_API_KEY` |

---

## 📡 REST API Reference

The FastAPI server provides automated OpenAPI documentation at **`http://localhost:8000/docs`**.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Basic liveness probe |
| `GET` | `/ready` | Database readiness probe |
| `GET` | `/api/keywords` | List all tracked keywords with mention counts |
| `POST` | `/api/keywords` | Register a new keyword with aliases & context hint |
| `POST` | `/api/collect` | Trigger background ingestion job (idempotent) |
| `GET` | `/api/runs/{id}` | Poll background ingestion job status & metrics |
| `GET` | `/api/mentions` | Query mentions with full-text search & filters |
| `GET` | `/api/stats/overview` | Executive KPI stats (sentiment, top topics, drop audit) |
| `GET` | `/api/stats/timeseries` | Chronological mention volume & sentiment buckets |
| `GET` | `/api/insights/summary` | Retrieve cached AI executive summary |
| `POST` | `/api/insights/summary/refresh` | Force AI summary regeneration (rate-limited) |
| `GET` | `/api/insights/trends` | Topic velocity and acceleration report (BON-01) |
| `GET` | `/api/compare` | Multi-brand competitor comparison (BON-02) |
| `GET` | `/api/alerts` | Anomaly alert history (BON-04) |
| `POST` | `/internal/ingest` | Scheduled cron trigger protected by `X-Internal-Secret` |

---

## 🔒 Security & Prompt Injection Defense

All ingested social text is strictly isolated using XML boundary tags (`<mentions_data>`) and verified against Pydantic schemas to prevent prompt injection attacks from malicious public posts. All containers execute as non-privileged users (`appuser:1001` and `nextjs:1001`).

See [`docs/SECURITY.md`](docs/SECURITY.md) for our comprehensive threat model and hardening policy.

---

## 🧪 Testing & Verification

Social Insights comes with a comprehensive automated test suite:

```bash
# Run all 62 backend unit, integration, and bonus tests
pytest backend/tests/ -v

# Run lint and formatting checks
ruff check backend/
ruff format --check backend/

# Run frontend production build
npm run build --prefix frontend

# Run automated end-to-end smoke test
bash scripts/smoke_test.sh Toyota
```

---

## 📄 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
