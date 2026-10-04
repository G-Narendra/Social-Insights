# Social Insights — System Architecture & Engineering Design

## 1. System Overview & Component Diagram

Social Insights is an end-to-end, cost-engineered social listening platform designed to track brands, products, and keywords across decentralized web sources (Hacker News, Google News RSS, Reddit, YouTube, Stack Exchange). Rather than indiscriminately feeding raw social data into costly Large Language Models, Social Insights implements a **Tiered Intelligence Architecture** that leverages deterministic algorithms, lightweight CPU-optimized neural models, and targeted LLM calls strictly on aggregated or low-confidence data.

```
                         [ USER / BROWSER ]
                                 │
                                 ▼
                     [ Next.js 14 Web UI ]
                     (Tailwind, TypeScript)
                                 │
                                 ▼ HTTP REST / SSE
           ┌───────────────────────────────────────────────┐
           │        FastAPI Application Server             │
           │  ┌───────────────┐   ┌─────────────────────┐  │
           │  │ API Endpoints │   │ Background Services │  │
           │  │ /api/collect  │   │ & Task Coordinator  │  │
           │  │ /api/mentions │   └──────────┬──────────┘  │
           │  │ /api/stats    │              │             │
           │  └───────┬───────┘              │             │
           └──────────┼──────────────────────┼─────────────┘
                      │                      │
       ┌──────────────┴───────────────┐      │
       ▼                              ▼      ▼
┌──────────────┐             ┌──────────────────────────────────┐
│  PostgreSQL  │             │   Multi-Source Ingestion Layer   │
│  or SQLite3  │             │  ┌──────────────┐┌─────────────┐ │
│  (SQLAlchemy)│             │  │ Hacker News  ││ Google News │ │
└──────────────┘             │  │ Algolia API  ││ RSS Feed    │ │
                             │  └──────────────┘└─────────────┘ │
                             │  ┌──────────────┐┌─────────────┐ │
                             │  │ Reddit API   ││ YouTube API │ │
                             │  │ (OAuth)      ││ (Data v3)   │ │
                             │  └──────────────┘└─────────────┘ │
                             └────────────────┬─────────────────┘
                                              │ RawMention[]
                                              ▼
                             ┌──────────────────────────────────┐
                             │    Processing & Quality Engine   │
                             │  - NFKC Normalization & Unidecode│
                             │  - Canonical URL Extraction      │
                             │  - Exact Hash & Near-Dedup       │
                             │  - Boundary Relevance Filtering  │
                             │  - Spam / Quality Heuristics     │
                             └────────────────┬─────────────────┘
                                              │ Processed Mentions
                                              ▼
                             ┌──────────────────────────────────┐
                             │    Tiered Intelligence Engine    │
                             │  Tier 0: Regex & Lexical Rules   │
                             │  Tier 1: Twitter-RoBERTa (Sent.) │
                             │          all-MiniLM-L6 (Topics)  │
                             │  Tier 2: NVIDIA NIM (Llama-3.1)  │
                             │  Tier 3: Template Fallbacks      │
                             └──────────────────────────────────┘
```

---

## 2. Tiered Intelligence Architecture

A primary design constraint is **zero-cost operation** and computational efficiency. Running an LLM over every individual tweet, comment, or article headline costs significant latency and API fees or compute footprint. Social Insights implements a 4-tier processing funnel:

| Tier | Component | Technology / Model | Latency | Financial Cost | Application Scope |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | Deterministic Rules | xxHash64, Regex, Word Boundaries, NFKC | < 0.1 ms | $0.00 | Exact dedup, URL canonicalization, spam pruning, keyword presence |
| **Tier 1** | CPU-Optimized Local NLP | `twitter-roberta-base-sentiment-latest` & `all-MiniLM-L6-v2` | 5–15 ms | $0.00 | 3-class sentiment, 8-class prototype topic embeddings, near-dedup |
| **Tier 2** | Targeted LLM Inference | NVIDIA NIM API (`meta/llama-3.1-8b-instruct`) / Ollama | 400–1200 ms | Free tier | Ambiguity resolution for low confidence (<0.55), high-level summaries & insights |
| **Tier 3** | Deterministic Fallback | Statistical Aggregation & Template Synthesizer | < 1 ms | $0.00 | Executive summaries and insights when offline or LLM quotas are exhausted |

### Cost & Latency Analysis: Why Not "LLM for Everything"?

1. **Token Cost Explosion**: Ingestion of 1,000 mentions at an average of 150 tokens = 150,000 prompt tokens + 50,000 completion tokens. For commercial APIs, this quickly incurs $0.50–$2.00 per keyword collection. At 50 keywords daily, costs reach $25–$100/day.
2. **Throughput Bottlenecks**: LLM API calls with network roundtrips require 500ms–2000ms per request. Even with concurrency, processing 1,000 mentions takes minutes and hits rate limits (429). Tier 1 local models process in batches of 32 on standard modern CPUs at >150 items/sec.
3. **Auditable Confidence**: Deterministic rules and calibrated softmax probabilities provide transparent, reproducible scores, preventing hallucinations in classification metrics.

---

## 3. Data Pipeline State Machine

Mentions advance through explicit, persisted lifecycle states. A failure at any point preserves progress and prevents re-ingestion of already processed items.

```
                    ┌─────────────────────────┐
                    │      1. COLLECTED       │
                    │   (Ingested from API)   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      2. NORMALIZED      │
                    │ (HTML stripped, NFKC)   │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
     Duplicate?                                     │ Unique
              ▼                                     ▼
      [ DROPPED: dup ]                    ┌──────────────────┐
                                          │    3. DEDUPED    │
                                          └─────────┬────────┘
                                                    │
                                ┌───────────────────┴───────────────────┐
                       Irrelevant / Spam?                               │ Relevant
                                ▼                                       ▼
                     [ DROPPED: irrelevant ]                 ┌──────────────────┐
                     [ DROPPED: spam       ]                 │   4. RELEVANT    │
                                                             └─────────┬────────┘
                                                                       │
                                                                       ▼
                                                             ┌──────────────────┐
                                                             │   5. ENRICHED    │
                                                             │(Sentiment, Topic)│
                                                             └─────────┬────────┘
                                                                       │
                                                                       ▼
                                                             ┌──────────────────┐
                                                             │     6. DONE      │
                                                             │ (Dashboard Ready)│
                                                             └──────────────────┘
```

Every dropped mention stores a specific `drop_reason` (`duplicate_hash`, `duplicate_url`, `irrelevant_keyword`, `too_short`, `spam_link_density`, `non_english`), ensuring full auditability for data quality analytics.

---

## 4. Database Schema & Indexing Strategy

The data layer uses SQLAlchemy 2.0 with async engine support (`aiosqlite` for local dev/testing, `asyncpg` for PostgreSQL/Supabase production).

### Key Entities:
- **`keywords`**: Central tracking entity storing search terms, aliases (JSON), context hints for disambiguation, and collection cadence metadata.
- **`collection_runs`**: Tracks execution lifecycle (`queued`, `running`, `partial`, `succeeded`, `failed`), execution timestamps, per-source item counts, and error telemetry.
- **`mentions`**: Core analytical entity storing raw and sanitized text, canonical URLs, publication and collection timestamps, author handles, engagement metrics, pipeline status, sentiment scores, and topic classifications.
- **`summaries`**: Versioned, cached intelligence digests tied to a keyword and a `data_fingerprint` hash. Prevents regeneration overhead when underlying data hasn't changed.
- **`alerts`**: Detected anomalies (e.g., negative sentiment volume spikes > 2 standard deviations over a 14-day rolling baseline).

### Indexing Rationale:
1. `UNIQUE INDEX idx_mentions_source_source_id ON mentions (source, source_id)`: Guarantees idempotent ingestion at the database boundary.
2. `INDEX idx_mentions_keyword_published ON mentions (keyword_id, published_at)`: Accelerates time-series queries and chronological timeline rendering.
3. `INDEX idx_mentions_keyword_sentiment ON mentions (keyword_id, sentiment)` & `INDEX idx_mentions_keyword_topic ON mentions (keyword_id, topic)`: Enables single-roundtrip aggregation for dashboard stat cards and distributions without table scans.
4. `INDEX idx_mentions_content_hash ON mentions (content_hash)`: Accelerates exact duplicate lookups during Tier 0 processing.

---

## 5. Architectural Decisions Log

| Date | Decision | Alternatives Considered | Justification |
| :--- | :--- | :--- | :--- |
| **2026-10-05** | **NVIDIA NIM API** for LLM Provider | Local Ollama, Hugging Face Serverless, Groq | Zero-cost tier with fast response times and generous developer credits. Provides standard OpenAI-compatible API without local GPU or Docker requirements on host. |
| **2026-10-05** | **`cardiffnlp/twitter-roberta-base-sentiment-latest`** for Sentiment | VADER, TextBlob, FinBERT, DistilBERT-SST2 | Trained directly on 124M+ tweets with modern slang, emojis, and social phrasing. 3-class distribution (negative, neutral, positive) maps directly to requirements. Highly optimized ONNX/Torch CPU inference. |
| **2026-10-05** | **`sentence-transformers/all-MiniLM-L6-v2`** for Topic Prototypes | LDA / NMF, Zero-shot BART-large-MNLI, TF-IDF | MiniLM generates compact 384-dimensional embeddings in ~5ms on CPU. Cosine similarity against topic prototype centroids provides accurate classification with zero prompt overhead and deterministic behavior. |
| **2026-10-05** | **FastAPI + Async SQLAlchemy 2.0** for Backend | Flask, Django, Express.js | Native async I/O handles concurrent external HTTP requests to multiple social APIs simultaneously without blocking. First-class Pydantic v2 validation ensures robust API contracts. |
| **2026-10-05** | **Next.js 14 App Router + Tailwind** for Frontend | Vite + React SPA, Streamlit | Server-side rendering options, robust routing, production performance, and component-level reusability. Clean, modern responsive dashboard design. |

---

## 6. Scaling & Resilience Analysis

### Potential Failure Points & Mitigations:
1. **Third-Party Source Rate Limits (HTTP 429)**:
   - *Mitigation*: Per-source token bucket rate limiting with exponential backoff and jitter. Circuit breakers disable problematic sources temporarily without failing the collection run.
2. **Memory Constraints on Free Hosting (e.g., Hugging Face Spaces 16GB / Render 512MB)**:
   - *Mitigation*: Lazy loading of models; PyTorch CPU threads restricted (`torch.set_num_threads(2)`); embedding batches capped at 32; cached summary lookups to minimize runtime allocations.
3. **Ambiguous Keywords (e.g., "Apple", "Meta", "Target")**:
   - *Mitigation*: Multi-stage disambiguation using `context_hint` stored in `keywords` table. Mentions must pass keyword boundary checks and embedding similarity checks before qualification.
4. **Cold-Start Latency**:
   - *Mitigation*: Lightweight frontend states indicating "Backend is warming up" with progressive polling; persistent SQLite / Postgres connections via pooling.
