# Social Insights

> **Enterprise-Grade, Open-Source Social Listening & Market Intelligence Platform with Tiered AI.**  
> Real-time brand monitoring, voice-of-customer synthesis, competitor benchmarking, and statistical anomaly detection across 8 decentralized data sources — with zero required API fees.

[![GitHub Repo](https://img.shields.io/badge/GitHub-G--Narendra%2FSocial--Insights-181717?style=flat&logo=github)](https://github.com/G-Narendra/Social-Insights)
[![Tests Passing](https://img.shields.io/badge/tests-69%20passed-brightgreen.svg?style=flat)](backend/tests/)
[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg?style=flat&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

---

## 📑 Table of Contents

- [Overview & Value Proposition](#-overview--value-proposition)
- [System Architecture](#-system-architecture)
- [Tiered AI Intelligence Funnel](#-tiered-ai-intelligence-funnel)
- [Supported Ingestion Connectors](#-supported-ingestion-connectors)
- [Core Platform Capabilities](#-core-platform-capabilities)
- [Empirical AI Benchmarks](#-empirical-ai-benchmarks)
- [Quickstart Guide (Local Development)](#-quickstart-guide-local-development)
- [Docker & Containerized Deployment](#-docker--containerized-deployment)
- [Production Deployment Guide](#-production-deployment-guide)
  - [Architecture Pattern A: Modern PaaS (Vercel + Render + Neon)](#pattern-a-modern-paas-recommended)
  - [Architecture Pattern B: Self-Hosted VPS (Docker Compose + Caddy SSL)](#pattern-b-self-hosted-vps-single-box)
- [Environment Configuration Matrix](#-environment-configuration-matrix)
- [REST API Reference](#-rest-api-reference)
- [Security & Prompt Injection Hardening](#-security--prompt-injection-hardening)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [License](#-license)

---

## 🌟 Overview & Value Proposition

Traditional enterprise social listening solutions (e.g., Brandwatch, Sprinklr, Sprout Social) cost upwards of $10,000–$60,000 annually. Conversely, naive open-source prototypes send raw internet scrapes directly to commercial LLM APIs, resulting in exorbitant token bills, rate limits, latency bottlenecks, and vulnerability to prompt injection.

**Social Insights** solves this with an **intelligent, cost-optimized, tiered architecture**:

1. **Multi-Domain Brand Monitoring**: Track any brand, product, technology, or topic (Automotive, Consumer Tech, SaaS, Web3, Open Source, Healthcare, Fashion, etc.).
2. **Context-Aware Deduplication & False-Positive Shielding**: Regex word-boundary filtering, domain-specific negative keywords, and contextual hints prevent cross-entity confusion (e.g., disambiguating *OpenAI ChatGPT* from unrelated car or bot mentions).
3. **8 Global Ingestion Connectors**: Continuously collects discussions, news, issues, and video transcripts without requiring paid subscriptions.
4. **$0.00 Local Neural Inference Baseline**: Heavy sentiment classification and topic clustering run on local CPUs with sub-15ms latency.
5. **Targeted LLM Synthesis**: State-of-the-art vision/text models (e.g., NVIDIA NIM Llama 3.2 11B / 3.1 8B or local Ollama) are invoked exclusively for executive synthesis and low-confidence edge cases.
6. **100% Offline Resiliency**: Deterministic analytics engine produces fact-based, zero-hallucination executive intelligence even when cloud APIs are disconnected or rate-limited.

---

## 🏗️ System Architecture

```
                                  [ Global Ingestion Sources ]
                                                │
    ┌──────────────┬──────────────┬─────────────┴┬─────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼             ▼              ▼              ▼
[Google News] [Hacker News] [Stack Exchange] [Wikipedia] [LinkedIn Pulse] [GitHub Issues] [Reddit/YouTube]
    │              │              │              │             │              │              │
    └──────────────┴──────────────┴──────┬───────┴─────────────┴──────────────┴──────────────┘
                                         │ Raw Social Mentions
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │           FastAPI Ingestion Engine        │
                   │  - Exponential Backoff & Fault Isolation  │
                   │  - Idempotent Job Locking (Alembic/Async) │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │                               TIERED INTELLIGENCE PIPELINE                                │
 │                                                                                           │
 │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │ Tier 0: Deterministic Ingestion Filter (<0.1ms)                                     │  │
 │  │  • URL Tracking Stripper (`utm_*`, `fbclid`, `gclid`) & Canonicalization            │  │
 │  │  • xxHash64 Content Hashing & Exact Duplicate Elimination                           │  │
 │  │  • Strict Regex Word-Boundary Match & Negative Keyword Anti-Collision Filter        │  │
 │  │  • FastText / LangDetect English Language Verification                              │  │
 │  └──────────────────────────────────────────┬──────────────────────────────────────────┘  │
 │                                             │ Clean, Relevant Mentions                    │
 │                                             ▼                                             │
 │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │ Tier 1: Local Neural Classification (CPU Batched, 5–15ms, $0.00 Cost)               │  │
 │  │  • Sentiment: `cardiffnlp/twitter-roberta-base-sentiment-latest` (85.0% Accuracy)   │  │
 │  │  • Topics: `sentence-transformers/all-MiniLM-L6-v2` Embedding Cosine Space (75.0%)  │  │
 │  │  • Softmax Entropy & Confidence Thresholding (<0.55 triggers low-confidence flag)   │  │
 │  └──────────────────────┬───────────────────────────────────────────┬──────────────────┘  │
 │                         │                                           │                     │
 │                         │ High-Confidence Data                      │ Edge-Cases & Syntheses
 │                         ▼                                           ▼                     │
 │  ┌──────────────────────────────────────────────┐  ┌───────────────────────────────────┐  │
 │  │ SQLite (WAL) / Managed PostgreSQL (asyncpg)  │  │ Tier 2: NVIDIA NIM / OpenAI LLM   │  │
 │  │ Mentions, Keywords, Runs, & Trend Baselines  │  │  • Compact XML Sandboxing         │  │
 │  └──────────────────────┬───────────────────────┘  │  • Executive VoC Synthesis Cards  │  │
 │                         │                          └─────────────────┬─────────────────┘  │
 │                         │                                            │ (If Offline)       │
 │                         │                                            ▼                    │
 │                         │                          ┌───────────────────────────────────┐  │
 │                         │                          │ Tier 3: Deterministic Engine      │  │
 │                         │                          │  • Zero-Hallucination Fallback    │  │
 │                         │                          └─────────────────┬─────────────────┘  │
 │                         │                                            │                    │
 │                         └────────────────────┬───────────────────────┘                    │
 └──────────────────────────────────────────────┼────────────────────────────────────────────┘
                                                │ REST API / JSON Telemetry
                                                ▼
                   ┌───────────────────────────────────────────┐
                   │          Next.js 14 Web Dashboard         │
                   │  - Responsive Glassmorphism & Dark Mode   │
                   │  - NPS Brand Reputation Health Index      │
                   │  - Topic Velocity & Anomaly Alert Banner  │
                   │  - Competitor Benchmark & Triage Feed     │
                   └───────────────────────────────────────────┘
```

---

## 🧠 Tiered AI Intelligence Funnel

Social Insights splits intelligence workloads into four distinct tiers to optimize **accuracy, speed, cost, and reliability**:

| Tier | Engine / Model | Execution Latency | Cost per 1K Mentions | Role & Responsibility |
|---|---|---|---|---|
| **Tier 0** | Regex, URL Canonicalizer, xxHash, LangDetect | `< 0.1 ms` | **$0.00** | Drops spam, eliminates near-duplicates, strips tracking parameters, and applies negative keyword filters. |
| **Tier 1** | CardiffNLP RoBERTa + Sentence-Transformers MiniLM | `5 – 15 ms` | **$0.00** | High-throughput local CPU classification. Classifies sentiment (Positive, Neutral, Negative) and maps content into 8 canonical topic vectors. |
| **Tier 2** | NVIDIA NIM API (`meta/llama-3.2-11b-vision-instruct` / `3.1-8b`) | `400 – 1200 ms` | `< $0.002` | Triggered only for high-level executive summaries and ambiguous classifications. Structured into 5 intelligence themes. |
| **Tier 3** | Deterministic Aggregation Engine | `< 5 ms` | **$0.00** | Failsafe analytics engine that aggregates real-time metrics, top pain points, and praises without hallucinations if cloud APIs are offline. |

---

## 🔌 Supported Ingestion Connectors

Social Insights ships with **8 production-ready connectors**, each equipped with exponential backoff retries, rate-limiting handlers, and timeout guards:

| Connector | Mechanism | Default State | Authentication | Data Ingested |
|---|---|---|---|---|
| **Google News** | RSS Atom Feed Aggregator | Active | None (Public) | Global journalism, syndicated articles, press releases |
| **Hacker News** | Algolia REST API | Active | None (Public) | Engineering sentiment, launch feedback, technical critique |
| **Wikipedia** | MediaWiki REST Search API | Active | None (Public) | Encyclopedic updates, controversies, leadership changes |
| **LinkedIn Pulse** | Curated RSS Syndication | Active | None (Public) | B2B commentary, corporate announcements, hiring feedback |
| **GitHub** | REST API v3 (Discussions & Issues) | Active | None (Optional Token) | Developer bugs, feature requests, repository discussions |
| **Stack Exchange** | REST API v2.3 | Active | None (Optional Key) | Technical troubleshooting, API complaints, developer sentiment |
| **Reddit** | Public JSON & OAuth2 API | Active | Optional OAuth | Community feedback, unfiltered product reviews, niche discussions |
| **YouTube** | YouTube Data API v3 | Active | Optional API Key | Video titles, creator reviews, tech teardowns |

---

## 🚀 Core Platform Capabilities

### 1. Brand Reputation Health Index (NPS Normalized)
Aggregates mention sentiment into an industry-standard 0–100 index paired with the **Net Sentiment Score (NSS = %Positive − %Negative)**:
- **0–20**: *Critical Friction* (Immediate intervention required)
- **21–40**: *Vulnerable* (Elevated negative feedback)
- **41–60**: *Balanced Neutral* (Equilibrium across mentions)
- **61–80**: *Strong Affinity* (Healthy organic advocacy)
- **81–100**: *High Advocacy* (Market-leading brand perception)

### 2. Topic Velocity & Trend Acceleration Engine
Continuously tracks topic volume shifts over a rolling 7-day sliding window. Detects accelerating themes (e.g., `+1450% velocity on customer support`) so product teams can intervene before a crisis escalates.

### 3. Statistical Anomaly & Sentiment Spike Alerts
Monitors a 14-day rolling baseline for each brand ($\mu$ and $\sigma$). Automatically triggers an **Urgent Anomaly Alert** when the negative sentiment ratio or volume diverges by more than **2 standard deviations ($2\sigma$)**.

### 4. Multi-Brand Competitor Benchmarking
Select any tracked brand to compare side-by-side:
- Relative mention volume & Share of Voice (SOV %)
- Cross-brand sentiment distribution
- Clustered competitor complaint themes

### 5. Quick Triage & Multi-Attribute Mentions Feed
Full-text search with instant filter chips:
- 🚨 **Urgent Negatives**: High-friction feedback requiring fast support response
- ⭐ **High Praise**: Organic user testimonials and product wins
- 🛠️ **Bugs & Issues**: Technical flaws, defects, and glitches
- 💬 **Support Requests**: Onboarding, configuration, and troubleshooting inquiries
- 💰 **Pricing & Billing**: Feedback regarding pricing tiers, subscription changes, and value

### 6. Dynamic Keyword Management with Collision Defense
Create brands with aliases, contextual disambiguation hints, and negative exclusion keywords. Deleting a brand executes an atomic cascade that purges all associated mentions, metrics, and cached summaries cleanly.

---

## 📊 Empirical AI Benchmarks

Evaluated against 100 hand-labeled social media benchmark samples ([`backend/eval/labelled_sample.jsonl`](backend/eval/labelled_sample.jsonl)):

| Metric | Measured Score | Target Threshold | Status |
|---|---|---|---|
| **Sentiment Classification Accuracy** | **85.00%** | > 75.0% | ✅ Exceeded (+10.0%) |
| **Sentiment Macro F1-Score** | **0.8496** | > 0.70 | ✅ Exceeded (+0.15) |
| **Topic Categorization Accuracy** | **75.00%** | > 70.0% | ✅ Exceeded (+5.0%) |
| **Topic Macro F1-Score** | **0.7089** | > 0.65 | ✅ Exceeded (+0.06) |
| **Sentiment Inference Speed** | **~1.9 items/sec** | CPU Batched | ✅ Verified |
| **Topic Inference Speed** | **~7.5 items/sec** | CPU Batched | ✅ Verified |
| **LLM Inference Share** | **< 5% of items** | Tier 2 Strict Budgeting | ✅ Cost Optimized |
| **Automated Test Suite** | **69 / 69 passing** | 100% test pass rate | ✅ Verified |

---

## ⚡ Quickstart Guide (Local Development)

### 1. Prerequisites
- **Python**: 3.12+
- **Node.js**: 18.x or 20.x+
- **Git**

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/G-Narendra/Social-Insights.git
cd Social-Insights

# Create and activate Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment configuration
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI backend (http://127.0.0.1:8000)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
In a new terminal window:
```bash
cd Social-Insights/frontend

# Install npm dependencies
npm install

# Start development server (http://localhost:3000)
npm run dev
```

Visit **[http://localhost:3000](http://localhost:3000)** in your browser!

---

## 🐳 Docker & Containerized Deployment

Run the complete multi-container production stack with a single command:

```bash
# 1. Prepare environment variables
cp .env.example .env

# 2. Build and launch Backend + Frontend containers
docker compose up -d --build

# 3. Check health status
docker compose ps
curl -f http://localhost:8000/health
```

### Optional Docker Profiles
```bash
# Run with managed PostgreSQL 16
docker compose --profile postgres up -d

# Run with local Ollama offline LLM
docker compose --profile ollama up -d
```

---

## 🌐 Production Deployment Guide

Deploying Social Insights to production can be accomplished using either a **Modern PaaS Stack** (serverless frontend + managed backend) or a **Self-Hosted VPS** (Docker Compose + Reverse Proxy).

---

### Pattern A: Modern PaaS (Recommended)

This architecture provides high availability, automatic SSL, zero server maintenance, and generous free tiers.

```
 [Users] ──── HTTPS ────► [Vercel: Next.js Frontend]
                                │ (API Calls)
                                ▼
 [Managed Postgres] ◄───► [Render / Railway / Fly.io: FastAPI Backend]
 (Neon / Supabase)              │
                                ▼
                     [NVIDIA NIM / Public APIs]
```

#### Step 1: Provision Managed Database (Neon or Supabase)
1. Create a free account at [Neon.tech](https://neon.tech) or [Supabase.com](https://supabase.com).
2. Create a new PostgreSQL database named `social_insights`.
3. Copy your async connection string. It will look like:
   ```env
   DATABASE_URL=postgresql+asyncpg://user:password@ep-sample-123.region.neon.tech/social_insights?ssl=require
   ```

#### Step 2: Deploy Backend to Render, Railway, or Fly.io
Here are the steps for **Render.com** (similar on Railway or Fly.io):
1. Go to [Render Dashboard](https://dashboard.render.com/) -> **New +** -> **Web Service**.
2. Connect your GitHub repository: `https://github.com/G-Narendra/Social-Insights`.
3. Configure the service settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r ../requirements.txt && alembic -c ../alembic.ini upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   ```env
   APP_ENV=production
   DATABASE_URL=postgresql+asyncpg://user:password@ep-sample-123.region.neon.tech/social_insights?ssl=require
   CORS_ORIGINS=https://your-frontend.vercel.app
   INTERNAL_SECRET=generate-a-strong-random-uuid-here
   NVIDIA_API_KEY=your_nvidia_api_key_optional
   NVIDIA_MODEL=meta/llama-3.2-11b-vision-instruct
   HF_HOME=/tmp/huggingface
   SENTENCE_TRANSFORMERS_HOME=/tmp/sbert
   ```
5. Click **Create Web Service**. Note your backend URL (e.g., `https://social-insights-api.onrender.com`).

#### Step 3: Deploy Frontend to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/) -> **Add New** -> **Project**.
2. Import repository `G-Narendra/Social-Insights`.
3. Configure Project:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Select `frontend`
4. Add Environment Variable:
   ```env
   NEXT_PUBLIC_API_URL=https://social-insights-api.onrender.com
   ```
5. Click **Deploy**. Your dashboard is now live with global edge CDN and automatic SSL!

---

### Pattern B: Self-Hosted VPS (Single Box)

For full data sovereignty and $0 recurring cloud software costs, deploy to a $6–$12/month VPS (DigitalOcean Droplet, Hetzner Cloud, Linode, or AWS EC2) running Ubuntu 22.04/24.04 LTS.

#### Step 1: VPS Initial Provisioning
```bash
# SSH into your server
ssh root@your-server-ip

# Update packages and install Docker + Docker Compose + Caddy
apt update && apt upgrade -y
apt install -y git curl docker.io docker-compose-plugin caddy
systemctl enable --now docker
```

#### Step 2: Clone and Configure
```bash
cd /opt
git clone https://github.com/G-Narendra/Social-Insights.git
cd Social-Insights

# Generate environment configuration
cp .env.example .env
nano .env
```
Update your `.env` with:
```env
APP_ENV=production
DATABASE_URL=sqlite+aiosqlite:////app/data/social_insights.db
CORS_ORIGINS=https://insights.yourdomain.com
INTERNAL_SECRET=replace_with_strong_secret_key
NVIDIA_API_KEY=your_nvidia_key_if_available
```

#### Step 3: Launch Containers
```bash
docker compose up -d --build
```

#### Step 4: Configure Automatic HTTPS with Caddy
Edit `/etc/caddy/Caddyfile`:
```caddy
insights.yourdomain.com {
    # Reverse proxy Next.js frontend
    reverse_proxy localhost:3000

    # Reverse proxy backend API endpoints
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /health {
        reverse_proxy localhost:8000
    }
    handle /docs {
        reverse_proxy localhost:8000
    }
    handle /openapi.json {
        reverse_proxy localhost:8000
    }
}
```
Reload Caddy:
```bash
systemctl reload caddy
```
Caddy will automatically request and renew a free Let's Encrypt SSL certificate for `insights.yourdomain.com`.

---

## ⚙️ Environment Configuration Matrix

| Variable | Description | Default | Required? |
|---|---|---|---|
| `APP_ENV` | Application environment (`development`, `production`, `test`) | `development` | Yes |
| `DATABASE_URL` | SQLAlchemy async connection URI (`sqlite+aiosqlite` or `postgresql+asyncpg`) | `sqlite+aiosqlite:///./social_insights.db` | Yes |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:3000,http://127.0.0.1:3000` | Yes |
| `INTERNAL_SECRET` | Secret token to authenticate internal background cron jobs (`/internal/ingest`) | `dev-internal-secret` | Yes |
| `NEXT_PUBLIC_API_URL` | Frontend URL to route API calls to the backend | `http://127.0.0.1:8000` (or relative `""`) | Optional |
| `NVIDIA_API_KEY` | NVIDIA NIM API token for Tier 2 LLM synthesis ([Get Key](https://build.nvidia.com)) | `""` | Optional |
| `NVIDIA_MODEL` | LLM model identifier | `meta/llama-3.2-11b-vision-instruct` | Optional |
| `REDDIT_CLIENT_ID` | Reddit App Client ID for authenticated Reddit ingestion | `""` | Optional |
| `REDDIT_CLIENT_SECRET` | Reddit App Client Secret | `""` | Optional |
| `YOUTUBE_API_KEY` | Google Cloud API key with YouTube Data API v3 enabled | `""` | Optional |
| `HF_HOME` | Cache directory for local Hugging Face transformer models | `./.cache/huggingface` | Optional |
| `SENTENCE_TRANSFORMERS_HOME` | Cache directory for SBERT embedding models | `./.cache/sbert` | Optional |
| `TORCH_NUM_THREADS` | Number of CPU threads allocated to PyTorch local neural inference | `2` | Optional |

---

## 📡 REST API Reference

Automated interactive OpenAPI / Swagger documentation is available at `/docs` on any running backend instance.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Liveness health check |
| `GET` | `/ready` | Database readiness check & migration status |
| `GET` | `/api/keywords` | List all tracked brands/keywords with mention counts |
| `POST` | `/api/keywords` | Register a new brand with aliases, context hint, and negative keywords |
| `DELETE` | `/api/keywords/{id}` | Atomic purge of brand, mentions, alerts, and summaries |
| `POST` | `/api/collect` | Trigger asynchronous ingestion pipeline across all connectors |
| `GET` | `/api/runs/{id}` | Poll ingestion run status, items collected, and dropped count |
| `GET` | `/api/mentions` | Query mentions with full-text search, topic, sentiment, and triage filters |
| `GET` | `/api/stats/overview` | Executive KPI summary (sentiment share, top topics, dropped audit count) |
| `GET` | `/api/stats/timeseries` | Chronological mention volume and sentiment time series |
| `GET` | `/api/insights/summary` | Retrieve cached executive intelligence cards |
| `POST` | `/api/insights/summary/refresh` | Force AI executive summary re-synthesis (rate limited) |
| `GET` | `/api/insights/trends` | Topic velocity and acceleration metrics |
| `GET` | `/api/compare` | Multi-brand competitor comparison and complaint themes |
| `GET` | `/api/alerts` | Statistical anomaly and sentiment spike history |
| `POST` | `/internal/ingest` | Automated cron ingestion trigger (Protected by `X-Internal-Secret`) |

---

## 🔒 Security & Prompt Injection Hardening

- **Prompt Injection Defense**: Ingested social media text is never interpolated into LLM prompts as raw instructions. Content is isolated inside strictly bounded XML envelopes (`<mentions_data>`) with system prompt constraints prohibiting the execution of user instructions found in posts.
- **Pydantic Validation**: All API payloads and LLM responses are parsed and validated through strict Pydantic v2 schemas.
- **Non-Privileged Containers**: Production Docker images execute under unprivileged service users (`appuser:1001` and `nextjs:1001`).
- **Secret Sanitization**: Automated `.gitignore` rules prevent SQLite databases, `.env` files, model weights, and temporary scratch files from being committed.

---

## 🧪 Testing & Quality Assurance

Social Insights includes a thorough automated test suite covering unit logic, neural ML models, ingestion connectors, and full API integration:

```bash
# 1. Run all 69 backend unit and integration tests
pytest backend/tests/ -v

# 2. Run Ruff code quality and format inspection
ruff check backend/
ruff format --check backend/

# 3. Validate Frontend Next.js production build
cd frontend && npm run build
```

---

## 📄 License

This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for complete details.
