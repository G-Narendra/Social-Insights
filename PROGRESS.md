# PROGRESS

## Current status
Phase: 2  |  Role: Data Ingestion Engineer  |  Last update: 2026-10-05T01:45+05:30

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
- [ ] T2.1 SourceConnector abstract base
- [ ] T2.2 Shared HTTP client
- [ ] T2.3 Registry
- [ ] T2.4 Hacker News connector
- [ ] T2.5 Google News RSS connector
- [ ] T2.6 Reddit connector
- [ ] T2.7 YouTube connector
- [ ] T2.8 Stack Exchange connector (optional)
- [ ] T2.9 Orchestrator
- [ ] T2.10 Fixture tests

### Phase 3: Processing pipeline
- [ ] T3.1-T3.9 (not started)

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
