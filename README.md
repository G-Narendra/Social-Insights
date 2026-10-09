# Social Insights

> Open source social listening and tiered intelligence platform.
> It collects brand mentions across public sources, runs cost-controlled NLP and LLM processing, and presents reputation telemetry in an executive dashboard.

[![GitHub Repo](https://img.shields.io/badge/GitHub-G--Narendra%2FSocial--Insights-181717?style=flat&logo=github)](https://github.com/G-Narendra/Social-Insights)
[![Tests Passing](https://img.shields.io/badge/tests-78%20passed-brightgreen.svg?style=flat)](backend/tests/)
[![Python 3.12](https://img.shields.io/badge/python-3.12+-blue.svg?style=flat&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg?style=flat&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

---

## Table of contents

- [Overview and system goals](#overview-and-system-goals)
- [System architecture](#system-architecture)
- [Tiered intelligence funnel](#tiered-intelligence-funnel)
- [Supported ingestion connectors](#supported-ingestion-connectors)
- [Data cleaning and normalization](#data-cleaning-and-normalization)
- [Role-based access control](#role-based-access-control)
- [Frontend design system](#frontend-design-system)
- [Empirical benchmarks](#empirical-benchmarks)
- [Local development setup](#local-development-setup)
- [Containerized deployment](#containerized-deployment)
- [Production deployment guide](#production-deployment-guide)
- [Environment configuration matrix](#environment-configuration-matrix)
- [REST API reference](#rest-api-reference)
- [Security architecture](#security-architecture)
- [Testing and verification](#testing-and-verification)
- [License](#license)

---

## Overview and system goals

Social Insights provides continuous brand reputation telemetry, voice-of-customer synthesis, and statistical anomaly detection across public discussion sources without mandatory recurring API fees.

The system addresses specific engineering challenges:

1. **Container memory ceiling**: Backend execution stays strictly below 512 MB RAM to run on Render free instances. Setting `LOW_MEMORY_MODE = true` relies on fast heuristic classifiers and remote LLM endpoints rather than loading local transformer weights into memory. Under benchmark runs, process memory stays below 60 MB.
2. **Inference cost cap**: Keeps inference costs below $0.0001 per mention through a 4-tier funnel where inexpensive filters run before remote LLM invocations.
3. **Data cleanliness**: Rejects spam, affiliate links, and duplicate content through NFKC normalization, URL tracking parameter stripping, xxHash64 exact hashing, and Jaccard 3-gram text comparison (threshold 0.85).
4. **Role-based access control**: Enforces separate permissions for Administrators, Market Analysts, and Executive Viewers, with 1-click evaluation personas available on the login screen.

---

## System architecture

```
                                  [ Public Ingestion Sources ]
                                                │
    ┌──────────────┬──────────────┬─────────────┴┬─────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼             ▼              ▼              ▼
[Google News]  [Hacker News]  [Wikipedia]   [GitHub]   [Stack Exchange]   [Reddit]       [YouTube]
    │              │              │              │             │              │              │
    └──────────────┴──────────────┴──────┬───────┴─────────────┴──────────────┴──────────────┘
                                         │ Raw Social Mentions
                                         ▼
                   ┌───────────────────────────────────────────┐
                   │           FastAPI Ingestion Engine        │
                   │  - Concurrent Async HTTP Scrapers         │
                   │  - Fault Isolation & Per-Source Timeouts  │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │                               TIERED INTELLIGENCE PIPELINE                                │
 │                                                                                           │
 │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │ Tier 0: Fast Heuristics & Deterministic Cleaning (<0.1ms, $0.00 cost)               │  │
 │  │  • URL Tracking Stripper (utm_*, fbclid, gclid) and Canonicalization                │  │
 │  │  • xxHash64 Exact Hash and Jaccard 3-Gram Text Similarity (0.85 threshold)          │  │
 │  │  • Regex Word-Boundary Context Matching and Spam / Affiliate Keyword Filter         │  │
 │  │  • Lexical Sentiment Scoring and 8 Topic Centroids with Negation Handling           │  │
 │  └──────────────────────────────────────────┬──────────────────────────────────────────┘  │
 │                                             │ Clean Mentions                              │
 │                                             ▼                                             │
 │  ┌─────────────────────────────────────────────────────────────────────────────────────┐  │
 │  │ Tier 1: Local Embeddings (Optional, Bypassed in Low Memory Mode)                    │  │
 │  │  • CardiffNLP RoBERTa Sentiment Classification                                      │  │
 │  │  • Sentence-Transformers all-MiniLM-L6-v2 Topic Cosine Matching                     │  │
 │  └──────────────────────┬───────────────────────────────────────────┬──────────────────┘  │
 │                         │                                           │                     │
 │                         │ High-Confidence Records                   │ Low-Confidence /    │
 │                         │                                           │ Batch Synthesis     │
 │                         ▼                                           ▼                     │
 │  ┌──────────────────────────────────────────────┐  ┌───────────────────────────────────┐  │
 │  │ SQLite (WAL) or Managed PostgreSQL (asyncpg) │  │ Tier 2: Remote Frontier LLM       │  │
 │  │ Mentions, Keywords, Users, & Metrics Data    │  │  • NVIDIA NIM (Llama 3.2 11B)     │  │
 │  └──────────────────────┬───────────────────────┘  │  • XML Sandboxed Prompt Envelopes │  │
 │                         │                          └─────────────────┬─────────────────┘  │
 │                         │                                            │ Fallback           │
 │                         │                          ┌─────────────────┴─────────────────┐  │
 │                         │                          │ Tier 3: Deterministic Fallback    │  │
 │                         │                          │  • Structured Markdown Synthesis  │  │
 │                         │                          └─────────────────┬─────────────────┘  │
 │                         │                                            │                    │
 │                         └────────────────────┬───────────────────────┘                    │
 └──────────────────────────────────────────────┼────────────────────────────────────────────┘
                                                │ REST API / JWT Telemetry
                                                ▼
                   ┌───────────────────────────────────────────┐
                   │          Next.js 14 App Router UI         │
                   │  - Dark Slate Canvas (#0b0f19)            │
                   │  - Metric Ribbon (NSS, Brand Health)      │
                   │  - 5 Operational Tabs & Anomaly Alerts    │
                   │  - 1-Click Evaluation Persona Switcher    │
                   └───────────────────────────────────────────┘
```

---

## Tiered intelligence funnel

Social Insights divides intelligence processing into four sequential tiers to control operational costs and container memory:

| Tier | Engine | Latency | Cost per 1K Mentions | Operational role |
|---|---|---|---|---|
| **Tier 0** | Lexical rule classifier, regex centroids, xxHash64, Jaccard 3-gram | `< 0.1 ms` | **$0.00** | Drops duplicates, strips tracking parameters, and assigns heuristic sentiment and topic tags with zero memory overhead. |
| **Tier 1** | CardiffNLP RoBERTa and SentenceTransformers `all-MiniLM-L6-v2` | `5 to 15 ms` | **$0.00** | High-throughput local classification. Bypassed automatically when `LOW_MEMORY_MODE = true` to protect RAM limits. |
| **Tier 2** | NVIDIA NIM API (`meta/llama-3.2-11b-vision-instruct` or compatible) | `400 to 1200 ms` | `< $0.002` | Generates executive summaries, pain point categorizations, and leadership takeaways over batches of verified mentions. |
| **Tier 3** | Deterministic markdown template generator | `< 5 ms` | **$0.00** | Produces structured intelligence briefings directly from computed statistics when remote LLM keys are absent or rate-limited. |

---

## Supported ingestion connectors

The platform includes seven concurrent ingestion connectors:

1. **Google News RSS**: Collects syndicated news articles and press releases through public XML feeds.
2. **Hacker News**: Ingests technical critiques and product discussions using the Algolia search API.
3. **Wikipedia**: Tracks encyclopedic revisions, executive changes, and controversy records through the MediaWiki API.
4. **GitHub**: Collects issue reports and commit discussions using the GitHub REST API v3.
5. **Stack Exchange**: Tracks technical troubleshooting patterns and developer inquiries via REST API v2.3.
6. **Reddit**: Ingests public subreddit discussions and consumer feedback through public feeds or OAuth2.
7. **YouTube**: Retrieves video titles, creator descriptions, and review content via YouTube Data API v3.

---

## Data cleaning and normalization

Incoming mentions pass through a data cleaning pipeline before storage:

1. **NFKC Unicode normalization**: Standardizes varied character encodings, accents, and punctuation.
2. **URL parameter stripping**: Removes marketing tracking tokens (`utm_source`, `utm_medium`, `fbclid`, `gclid`) and hash fragments.
3. **xxHash64 exact deduplication**: Generates 64-bit non-cryptographic hashes of normalized text to discard duplicate posts instantly.
4. **Jaccard 3-gram text comparison**: Evaluates word 3-gram sets against recent collection windows with a 0.85 similarity threshold to drop syndicated copies.
5. **Quality and spam filtering**: Rejects items shorter than 30 characters or containing promotional spam patterns.

---

## Role-based access control

The application implements role-based access control (RBAC) across three distinct permission tiers:

1. **Administrator**: Full permissions, including brand deletion, system configuration, and data purging.
2. **Market Analyst**: Data collection triggers, AI insight refresh operations, and anomaly alert resolution.
3. **Executive Viewer**: Read-only access to dashboards, charts, and intelligence briefings. Mutation actions return HTTP 403 Forbidden.

### Evaluation personas

The login interface provides 1-click evaluation buttons that pre-seed credentials:
- `admin@socialinsights.io` (Role: Admin)
- `analyst@socialinsights.io` (Role: Analyst)
- `viewer@socialinsights.io` (Role: Viewer)

---

## Frontend design system

The frontend uses Next.js 14 App Router, Tailwind CSS, Lucide icons, and Recharts.

### Design tokens

- **Background**: Dark slate canvas (`#0b0f19`) with nested surface layers (`#111827`, `#1f2937`).
- **Accents**: Electric indigo (`#6366f1`) for primary actions, emerald (`#10b981`) for positive sentiment, amber (`#f59e0b`) for neutral sentiment, and rose (`#f43f5e`) for negative sentiment.
- **Borders and styling**: Subtle hairline borders (`border-white/10`) with backdrop blur (`backdrop-blur-md`).
- **Typography**: Clean sans-serif hierarchy with monospace tabular figures for numeric metrics.

### Dashboard layout

1. **Top navigation**: Project brand, active tracked keyword selector, role switcher badge, and live database latency indicator.
2. **Metric ribbon**: Displays Net Sentiment Score (-100 to +100), Brand Health Index (0 to 100), total mentions processed, and rejection rate.
3. **Operational tabs**:
   - **Overview**: Sentiment timelines, topic distributions, and source share donut charts with custom SVG tooltips.
   - **Mentions feed**: Searchable table with filtering by sentiment, topic, source, and confidence status.
   - **AI synthesis**: Structured executive takeaways, top pain points, and copyable markdown blocks.
   - **Competitor benchmark**: Side-by-side volume and sentiment comparison between tracked brands.
   - **System telemetry**: Container memory budget indicators, inference cost calculators, and connector health tables.
4. **Anomaly banner**: Displays volume surges and sentiment drops exceeding 2 standard deviations, with acknowledgement controls.

---

## Empirical benchmarks

Evaluated against 100 hand-labeled social media benchmark samples (`backend/eval/labelled_sample.jsonl`):

| Metric | Measured value | Target threshold | Result |
|---|---|---|---|
| **Sentiment classification accuracy** | **85.00%** | > 75.0% | Exceeded (+10.0%) |
| **Sentiment macro F1-score** | **0.8496** | > 0.70 | Exceeded (+0.15) |
| **Topic categorization accuracy** | **75.00%** | > 70.0% | Exceeded (+5.0%) |
| **Topic macro F1-score** | **0.7089** | > 0.65 | Exceeded (+0.06) |
| **Sentiment inference speed** | **~1.9 items/sec** | CPU Batched | Verified |
| **Topic inference speed** | **~7.5 items/sec** | CPU Batched | Verified |
| **Container memory in low memory mode** | **< 60 MB RAM** | < 512 MB | Verified |
| **Automated test suite** | **78 / 78 passing** | 100% pass rate | Verified |

---

## Local development setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Git

### Backend configuration

```bash
# Clone the repository
git clone https://github.com/G-Narendra/Social-Insights.git
cd Social-Insights

# Create and activate virtual environment
python -m venv .venv

# PowerShell (Windows):
.venv\Scripts\Activate.ps1
# Bash (Linux/macOS):
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Launch FastAPI development server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend configuration

```bash
# In a separate terminal window
cd Social-Insights/frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Open `http://localhost:3000` in your web browser.

---

## Containerized deployment

Run the complete multi-container stack locally or on a production host:

```bash
# Prepare environment variables
cp .env.example .env

# Build and start services
docker compose up -d --build

# Verify container status
docker compose ps
curl -f http://localhost:8000/health
```

### Optional Docker profiles

```bash
# Launch with PostgreSQL 16 container
docker compose --profile postgres up -d

# Launch with local Ollama inference container
docker compose --profile ollama up -d
```

---

## Production deployment guide

### Pattern A: Modern PaaS (Render and Vercel)

1. **Database**: Provision a serverless PostgreSQL instance on Neon or Supabase. Set `DATABASE_URL` with the `postgresql+asyncpg://` scheme.
2. **Backend on Render**:
   - Create a Web Service connected to the GitHub repository.
   - Set Root Directory to `backend`.
   - Set Docker build path to `Dockerfile`.
   - Set environment variables:
     - `APP_ENV=production`
     - `DATABASE_URL=postgresql+asyncpg://user:password@host/database?ssl=require`
     - `LOW_MEMORY_MODE=true`
     - `TORCH_NUM_THREADS=1`
     - `HF_HOME=/tmp/huggingface`
     - `SENTENCE_TRANSFORMERS_HOME=/tmp/sbert`
     - `INTERNAL_SECRET=your-random-secret-key`
     - `CORS_ORIGINS=https://your-frontend.vercel.app`
3. **Frontend on Vercel**:
   - Import the repository and select `frontend` as the root directory.
   - Set `NEXT_PUBLIC_API_URL` to your Render backend URL.
   - Deploy.

### Pattern B: Self-hosted VPS (Docker Compose and Caddy)

1. Provision an Ubuntu 22.04 or 24.04 LTS server.
2. Install Docker, Docker Compose, and Caddy.
3. Clone the repository and configure `.env`.
4. Run `docker compose up -d --build`.
5. Point Caddy to `localhost:3000` for frontend traffic and `localhost:8000` for `/api/*` and `/health`.

---

## Environment configuration matrix

| Variable | Description | Default | Required |
|---|---|---|---|
| `APP_ENV` | Application environment (`development`, `production`, `test`) | `development` | Yes |
| `DATABASE_URL` | SQLAlchemy async connection URI (`sqlite+aiosqlite` or `postgresql+asyncpg`) | `sqlite+aiosqlite:///./social_insights.db` | Yes |
| `LOW_MEMORY_MODE` | Disables heavy local model weights to stay under 512 MB RAM | `true` | Yes |
| `TORCH_NUM_THREADS` | Number of CPU threads allocated to PyTorch | `1` | Optional |
| `CORS_ORIGINS` | Comma-separated allowed CORS origins | `http://localhost:3000,http://127.0.0.1:3000` | Yes |
| `INTERNAL_SECRET` | Secret token to authenticate background cron jobs | `dev-internal-secret` | Yes |
| `NEXT_PUBLIC_API_URL` | Frontend URL to route API requests to the backend | `http://127.0.0.1:8000` | Optional |
| `NVIDIA_API_KEY` | NVIDIA NIM API token for Tier 2 LLM synthesis | `""` | Optional |
| `NVIDIA_MODEL` | LLM model identifier | `meta/llama-3.2-11b-vision-instruct` | Optional |
| `REDDIT_CLIENT_ID` | Client ID for authenticated Reddit ingestion | `""` | Optional |
| `REDDIT_CLIENT_SECRET` | Client Secret for authenticated Reddit ingestion | `""` | Optional |
| `YOUTUBE_API_KEY` | Google Cloud API key with YouTube Data API v3 enabled | `""` | Optional |

---

## REST API reference

OpenAPI interactive documentation is accessible at `/docs` on running backend instances.

| Method | Endpoint | Description | Permission |
|---|---|---|---|
| `GET` | `/health` | Liveness health probe | Public |
| `GET` | `/ready` | Database readiness and migration status | Public |
| `POST` | `/api/auth/signup` | Create user account with validated email and password | Public |
| `POST` | `/api/auth/login` | Authenticate existing user and issue JWT bearer token | Public |
| `POST` | `/api/auth/demo-login` | 1-click evaluation login for Admin, Analyst, or Viewer | Public |
| `GET` | `/api/auth/me` | Return authenticated user identity and role | Authenticated |
| `GET` | `/api/keywords` | List all tracked keywords with mention tallies | Viewer+ |
| `POST` | `/api/keywords` | Register new keyword with aliases and context hints | Analyst+ |
| `DELETE` | `/api/keywords/{id}` | Purge brand, mentions, alerts, and summaries | Admin |
| `POST` | `/api/collect` | Trigger asynchronous ingestion pipeline | Analyst+ |
| `GET` | `/api/runs/{id}` | Poll ingestion run status and progress metrics | Viewer+ |
| `GET` | `/api/mentions` | Query mentions with full-text search and filters | Viewer+ |
| `GET` | `/api/stats/overview` | Executive KPI summary and quality drop counts | Viewer+ |
| `GET` | `/api/stats/timeseries` | Chronological mention volume and sentiment buckets | Viewer+ |
| `GET` | `/api/insights/summary` | Retrieve cached executive intelligence cards | Viewer+ |
| `POST` | `/api/insights/summary/refresh` | Force AI executive summary regeneration | Analyst+ |
| `GET` | `/api/insights/trends` | Topic velocity and acceleration metrics | Viewer+ |
| `GET` | `/api/compare` | Multi-brand comparison and complaint themes | Viewer+ |
| `GET` | `/api/alerts` | Statistical anomaly and volume surge records | Viewer+ |
| `POST` | `/internal/ingest` | Background cron ingestion trigger (`X-Internal-Secret`) | Internal |

---

## Security architecture

1. **Authentication**: Uses standard library PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and RFC 7519 compliant HS256 JWT tokens.
2. **Prompt injection isolation**: Ingested social media text is enclosed within XML tags (`<mentions_data>`) with system instructions forbidding execution of user instructions found within raw posts.
3. **Input validation**: All payloads and responses are validated through Pydantic v2 schemas.
4. **Least privilege containers**: Docker images run under non-root users (`appuser:1001` and `nextjs:1001`).

---

## Testing and verification

Run the automated test suite locally:

```bash
# Execute backend test suite (78 tests)
pytest backend/tests/ -v

# Verify code formatting and linting
ruff check backend/
ruff format --check backend/

# Compile frontend production build
cd frontend && npm run build
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for terms.
