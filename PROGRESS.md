# PROGRESS

## Current status
Phase: 4  |  Role: ML / LLM Engineer  |  Last update: 2026-10-05T01:55+05:30

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
- [ ] T4.1-T4.11 (not started)

### Phase 5: API
- [ ] T5.1-T5.16 (not started)

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
(not yet measured)

## Human-only checklist
(to be filled in Phase 9/10)
