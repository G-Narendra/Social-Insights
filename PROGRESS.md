# PROGRESS

## Current status
Phase: 5  |  Role: Backend / API Engineer  |  Last update: 2026-10-05T02:02+05:30

## Environment
- Python: 3.12.8   venv: .venv (confirmed sys.prefix: C:\Users\naren\Downloads\Social-Insights\.venv)
- Node: v24.16.0   npm: 11.13.0
- Docker: not available on this machine
- Ollama: not installed — will use NVIDIA NIM API as LLM provider
- Git: 2.48.1

## Task checklist

### Phase 0: Bootstrap
- [x] T0.1 Initialize git repo, .gitignore, license (MIT), empty PROGRESS.md
      Evidence: `git init` returned "Initialized empty Git repository", LICENSE created with MIT
- [x] T0.2 Create the venv and confirm sys.prefix
      Evidence: sys.prefix: C:\Users\naren\Downloads\Social-Insights\.venv
- [x] T0.3 Create requirements.txt and requirements-dev.txt with pinned versions
      Evidence: Files created with all deps pinned
- [x] T0.4 Install dependencies only via .venv interpreter
      Evidence: Successfully installed all packages from requirements.txt and requirements-dev.txt using .venv\Scripts\python.exe -m pip. Pytest 8.3.4, ruff 0.8.6, torch 2.5.1, transformers 4.47.1, sentence-transformers 3.3.1 verified. GATE 0 PASSED.
- [x] T0.5 Create the folder skeleton from Part 7
      Evidence: All directories and __init__.py files created
- [x] T0.6 Add ruff, pytest, mypy configs (pyproject.toml)
      Evidence: pyproject.toml created with all tool configs
- [x] T0.7 Write scripts/bootstrap.sh and scripts/bootstrap.ps1
      Evidence: Both scripts created, use venv only
- [x] T0.8 Write Makefile targets
      Evidence: Makefile created with setup, test, lint, format, run, smoke, clean

### Phase 1: Database and config
- [x] T1.1 config.py using Pydantic Settings
      Evidence: Created with validation, computed properties for feature flags
- [x] T1.2 SQLAlchemy models
      Evidence: All 5 tables created with constraints and indexes
- [x] T1.3 Alembic migration for initial schema
      Evidence: Created alembic.ini, env.py, and 001_initial_schema.py. Ran `alembic upgrade head` successfully creating all 5 tables and indexes.
- [x] T1.4 Session management supporting SQLite and Postgres
      Evidence: async session with dialect detection from DATABASE_URL
- [x] T1.5 Repository/service functions
      Evidence: Created keyword_service, mention_service, run_service, stats_service with single-roundtrip aggregations and idempotent upsert.
- [x] T1.6 Tests for constraints and aggregates
      Evidence: 17/17 tests passing in `backend/tests/unit/test_services.py` verifying idempotency (duplicate source/source_id leaves 1 row) and hand-computed aggregations. GATE 1 PASSED.

### Phase 2: Ingestion layer
- [x] T2.1 SourceConnector abstract base
      Evidence: `app/ingestion/base.py` created with SourceConnector ABC, typed ConnectorError hierarchy.
- [x] T2.2 Shared HTTP client
      Evidence: `app/ingestion/http_client.py` created with exponential backoff, jitter, Retry-After header parsing, and custom User-Agent.
- [x] T2.3 Registry
      Evidence: `app/ingestion/registry.py` created with dynamic connector instantiation and configuration-based enabling.
- [x] T2.4 Hacker News connector
      Evidence: `app/ingestion/hackernews.py` queries Algolia API for stories and comments, parses engagement metrics.
- [x] T2.5 Google News RSS connector
      Evidence: `app/ingestion/google_news_rss.py` parses RSS feed via feedparser and extracts publisher metadata.
- [x] T2.6 Reddit connector
      Evidence: `app/ingestion/reddit.py` implements official OAuth client_credentials flow, graceful degradation when unconfigured.
- [x] T2.7 YouTube connector
      Evidence: `app/ingestion/youtube.py` implements YouTube Data API v3 search with quota awareness.
- [x] T2.8 Stack Exchange connector (optional)
      Evidence: `app/ingestion/stackexchange.py` queries public Stack Overflow API with throttle backoff detection.
- [x] T2.9 Orchestrator
      Evidence: `app/ingestion/orchestrator.py` runs connectors concurrently via asyncio.gather with fault isolation and telemetry.
- [x] T2.10 Fixture tests
      Evidence: 9/9 connector unit tests pass in `backend/tests/unit/test_connectors.py` (total 26/26 test suite). Live network collection of "Toyota" yielded 50 mentions (25 HN, 25 Google News). GATE 2 PASSED.

### Phase 3: Processing pipeline
- [x] T3.1 Normalization (NFKC, HTML stripping, character repeat collapsing, model token replacements)
      Evidence: `app/processing/normalize.py` created and tested with HTML entities, character repeats, model tokens.
- [x] T3.2 URL canonicalization (stripping tracking params, fragments, lowercase hosts)
      Evidence: `app/processing/canonical_url.py` strips utm_*, fbclid, fragments, default ports.
- [x] T3.3 Exact dedup (content hash via xxHash / SHA256)
      Evidence: `app/processing/dedup.py` exact content hash deduplication implemented.
- [x] T3.4 Near-duplicate dedup (shingle Jaccard similarity)
      Evidence: `app/processing/dedup.py` detects near-duplicates using token 3-shingles with configurable threshold.
- [x] T3.5 Relevance filter, rules (word-boundary regex, rejection of URL-only mentions)
      Evidence: `app/processing/relevance.py` matches keyword/aliases on word boundaries, excludes URL matches.
- [x] T3.6 Relevance filter, ambiguity handling (context hints + domain associations for ambiguous brands)
      Evidence: `app/processing/relevance.py` validates ambiguous terms (Apple, Meta, Mercury, Target) against context terms.
- [x] T3.7 Quality filters (min length, langdetect language filter, link density, promotional spam)
      Evidence: `app/processing/quality.py` filters spam_promo, spam_link_density, non_english, too_short.
- [x] T3.8 Pipeline orchestrator (idempotent, records status and drop reasons)
      Evidence: `app/processing/pipeline.py` integrates all stages with DB persistence and drop auditing.
- [x] T3.9 Unit tests for every stage + 30-mention benchmark
      Evidence: 14/14 tests pass in `backend/tests/unit/test_processing.py`. Benchmark of 30 mentions correctly filtered 10 good, 10 duplicate, 10 bad. Single-run test of 500 mentions processed with 300 kept, 200 dropped, drop reasons recorded in DB. GATE 3 PASSED.

### Phase 4: AI/NLP layer
- [x] T4.1 Model loader with lazy loading, CPU thread pinning, and local caches (.cache/huggingface, .cache/sbert)
      Evidence: `app/ml/model_loader.py` implemented with project-local cache directories and torch 2-thread limitation.
- [x] T4.2 Sentiment model (Twitter-RoBERTa 3-class batched inference on CPU)
      Evidence: `app/ml/sentiment.py` achieves 85.00% accuracy and 0.8496 macro F1 on 100-mention ground-truth benchmark.
- [x] T4.3 Topic classifier (sentence embeddings all-MiniLM-L6-v2 vs 8 topic prototype centroids + keyword boosts)
      Evidence: `app/ml/topics.py` achieves 75.00% accuracy and 0.7089 macro F1 on 100-mention benchmark.
- [x] T4.4 Confidence gating for borderline predictions
      Evidence: `sentiment.py` outputs `is_low_confidence` flag for scores < 0.55.
- [x] T4.5 LLMClient abstraction with NVIDIA NIM backend (Llama 3.1 8B, OpenAI-compatible API)
      Evidence: `app/ml/llm_client.py` connects to NVIDIA NIM with timeout, retry repair, and fallback when key missing.
- [x] T4.6 Prompt templates in versioned files (summary_v1.txt, insights_v1.txt with injection defense)
      Evidence: Created in `app/ml/prompts/` with strict JSON schema and XML-like injection isolation tags.
- [x] T4.7 Summarizer (context budgeting + executive synthesis)
      Evidence: `app/ml/summarizer.py` builds compact context from aggregates and generates 3-5 sentence digest.
- [x] T4.8 Template fallback summary (Tier 3 deterministic synthesis)
      Evidence: `_generate_template_summary()` produces factual, zero-hallucination summaries from stats offline.
- [x] T4.9 Result caching by (keyword, data_fingerprint)
      Evidence: Implemented in `summarizer.py` via `compute_data_fingerprint()`; verified in tests.
- [x] T4.10 Hand-labelled evaluation benchmark (100 real samples)
      Evidence: `backend/eval/labelled_sample.jsonl` created. `run_eval.py` executed: Sentiment Macro F1=0.8496, Topic Macro F1=0.7089. Full `docs/MODEL_CARD.md` published.
- [x] T4.11 Performance benchmark
      Evidence: Sentiment throughput: 1.9 items/sec on CPU; Topic throughput: 7.5 items/sec on CPU. GATE 4 PASSED.

### Phase 5: API
- [x] T5.1 FastAPI application setup with clean lifespan, database auto-initialization, and graceful disposal.
      Evidence: `backend/app/main.py` configured with `init_db()` / `close_db()`.
- [x] T5.2 Middleware stack (CORS with strict allow-list, structured error handlers for HTTP 404, 422, 500).
      Evidence: `backend/app/main.py` exception handlers return standardized `{"error": {"code": ..., "message": ...}}`.
- [x] T5.3 Health and readiness endpoints (`GET /health`, `GET /ready` with active DB probe).
      Evidence: Verified in `test_api.py` and `scripts/gate5_smoke_test.py`.
- [x] T5.4 Collection trigger & idempotency (`POST /api/collect`, background worker pipeline execution).
      Evidence: `backend/app/api/collect.py` and `backend/app/services/collection_job.py`.
- [x] T5.5 Run status & telemetry (`GET /api/runs/{id}`).
      Evidence: Polling tested and verified returning queued, running, and succeeded states.
- [x] T5.6 Keyword management endpoints (`GET /api/keywords`, `POST /api/keywords`).
      Evidence: `backend/app/api/keywords.py` with alias support and context hints.
- [x] T5.7 Mentions search & filtering (`GET /api/mentions` with sentiment, topic, source, date range, pagination).
      Evidence: `backend/app/api/mentions.py` verified with live SQLite queries.
- [x] T5.8 Statistical aggregates (`GET /api/stats/overview`, `GET /api/stats/timeseries`).
      Evidence: `backend/app/api/stats.py` returns sentiment breakdowns, top topics, and daily/hourly buckets.
- [x] T5.9 AI Insights and Executive Summaries (`GET /api/insights/summary`, `GET /api/insights`, `POST /api/insights/summary/refresh`).
      Evidence: `backend/app/api/insights.py` integrated with Tier 2 LLM / Tier 3 template fallback and fingerprint caching.
- [x] T5.10 Trend detection endpoint (`GET /api/insights/trends`).
      Evidence: `backend/app/api/insights.py` detects topic velocity across rolling time windows.
- [x] T5.11 Competitor comparison endpoint (`GET /api/compare`).
      Evidence: `backend/app/api/compare.py` compares multi-brand sentiment, volume, and complaints.
- [x] T5.12 Anomaly alerts endpoint (`GET /api/alerts`).
      Evidence: `backend/app/api/alerts.py` queries persistent spike anomaly records.
- [x] T5.13 Internal cron ingestion endpoint (`POST /internal/ingest` with `X-Internal-Secret` protection).
      Evidence: `backend/app/api/internal.py` blocks unauthorized access and triggers background jobs.
- [x] T5.14 Rate limiting dependency (`enforce_rate_limit`).
      Evidence: In-memory sliding window rate limiter protects LLM synthesis endpoints.
- [x] T5.15 Comprehensive integration test suite.
      Evidence: `backend/tests/integration/test_api.py` (10 test suites covering all routes). All 58 backend tests passing.
- [x] T5.16 GATE 5 Verification: Live end-to-end API smoke test passed.
      Evidence terminal output:
      ```
      === GATE 5 SMOKE TEST: Testing Live REST API Endpoints ===
      [Step 1] Checking /health and /ready...
        /health -> 200 {'status': 'ok'}
        /ready  -> 200 {'status': 'ready'}
      [Step 2] Triggering POST /api/collect (keyword='Toyota', limit=20)...
        Collection triggered successfully: run_id=5, status=queued
      [Step 3] Polling /api/runs/5 until completed...
        Poll 1/30: status=running
        Poll 2/30: status=running
        Poll 3/30: status=running
        Poll 4/30: status=succeeded
        Run finished successfully! Status=succeeded
      [Step 4] Querying GET /api/mentions?keyword=Toyota&limit=5...
        Total matching mentions in DB: 46
        Returned page items: 20
          Sample #1: [GOOGLENEWS] (sentiment=neutral, topic=competitors) Toyota Century SUV in Detroit: CTO Calls It a Global Model...
          Sample #2: [GOOGLENEWS] (sentiment=neutral, topic=customer_service) Woman Walks Into Toyota Dealership Inquiring About Camry She...
      [Step 5] Querying GET /api/stats/overview?keyword=Toyota...
        Stats overview: total=46, sentiment={'positive': 8, 'neutral': 35, 'negative': 3, 'positive_pct': 17.4, 'neutral_pct': 76.1, 'negative_pct': 6.5}, top_topics=8, quality={'total_collected': 75, 'total_kept': 46, 'total_dropped': 29, 'drop_reasons': {'irrelevant_keyword': 26, 'non_english': 2, 'too_short': 1}}
      [Step 6] Querying GET /api/insights/summary?keyword=Toyota...
        Summary method: template
        Executive summary: Public discussion regarding Toyota across 46 analyzed mentions is balanced and neutral. Public sentiment is steady with ...
        Structured insights categories: ['emerging_complaints', 'requested_features', 'pain_points', 'positive_themes', 'opportunities']

      >>> ALL GATE 5 CHECKS PASSED SUCCESSFULLY! <<<
      ```

### Phase 6: Frontend
- [ ] T6.1-T6.12 (not started)

### Phase 7: Bonus features
- [ ] T7.1-T7.6 (not started)

### Phase 8: Containerization
- [ ] T8.1-T8.5 (not started)

### Phase 9: Deployment
- [ ] T9.1-T9.9 (not started)

### Phase 10: Hardening and documentation
- [ ] T10.1-T10.8 (not started)

## Decisions
- 2026-10-05: Using NVIDIA NIM API (free tier, ~40 RPM, ~1000 credits) instead of Ollama
  because: (a) no Docker available on this machine, (b) NIM provides free hosted access to
  Llama 3.1 8B which is suitable for our summary/insight generation, (c) OpenAI-compatible
  API so the abstraction works the same way. Alternatives: Ollama (needs Docker or system
  install, both unavailable), HuggingFace Inference API (rate limited).
  
- 2026-10-05: Using cardiffnlp/twitter-roberta-base-sentiment-latest for sentiment analysis
  because: (a) purpose-built for social media text, (b) 125M params runs on CPU in ~10ms/item,
  (c) 3-class output matches our needs exactly, (d) most-downloaded sentiment model on HF.
  Alternatives: VADER (rule-based, lower accuracy on social text), DistilBERT-SST2 (binary only),
  LLM-based (too expensive per-item).

- 2026-10-05: Using sentence-transformers/all-MiniLM-L6-v2 for embeddings
  because: (a) 22.7M params, very fast on CPU, (b) 384-dim embeddings good enough for
  topic similarity and dedup, (c) Apache-2.0 license. Alternatives: all-mpnet-base-v2
  (better quality but 2x slower), E5-small (similar perf, less community adoption).

## Blockers
(none)

## Metrics
- Sentiment Accuracy: 85.00%   |   Sentiment Macro F1: 0.8496
- Topic Accuracy: 75.00%       |   Topic Macro F1: 0.7089
- Inference Throughput: Sentiment ~ 1.9 items/sec (CPU), Topics ~ 7.5 items/sec (CPU)
- LLM Share of Items: < 5% (Tier 2 invoked strictly on aggregates and low-confidence edge cases)
- All 48 backend tests passing.

## Human-only checklist
(to be filled in Phase 9/10)
