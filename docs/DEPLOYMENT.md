# Social Insights — Deployment Guide

This guide details deployment options for the Social Insights platform, ranging from single-server Docker Compose deployments to managed cloud platforms and hybrid serverless setups.

---

## 1. Quickstart: Docker Compose (Recommended for Production & VPS)

The easiest and most reproducible way to run Social Insights in production is via Docker Compose.

### Prerequisites
- Docker Engine 24.0+ and Docker Compose v2.20+
- At least 2GB of RAM (4GB recommended for caching Hugging Face models)
- Inbound ports `8000` (API) and `3000` (Frontend) or an external reverse proxy (Caddy/Nginx)

### Steps

1. **Clone the repository on your server:**
   ```bash
   git clone https://github.com/your-org/social-insights.git
   cd social-insights
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   # Edit .env to set your secrets and NVIDIA_API_KEY
   nano .env
   ```

3. **Launch with Docker Compose:**
   ```bash
   # Standard production launch (FastAPI + Next.js + SQLite volume)
   docker compose up -d --build

   # Verify running containers
   docker compose ps
   ```

4. **Verify Health:**
   ```bash
   curl -f http://localhost:8000/health
   curl -f http://localhost:8000/ready
   curl -f http://localhost:3000/
   ```

5. **Run the End-to-End Smoke Test:**
   ```bash
   bash scripts/smoke_test.sh Toyota
   ```

---

## 2. Using PostgreSQL (Optional Multi-User Production Database)

By default, the platform uses an embedded SQLite database stored in a persistent Docker volume (`backend_data`), which requires zero configuration and zero operational overhead.

If you prefer PostgreSQL:
1. Start the PostgreSQL container profile:
   ```bash
   docker compose --profile postgres up -d
   ```
2. Update `.env`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:postgres_secure_pass@db:5432/social_insights
   ```
3. Run migrations:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

---

## 3. Platform-as-a-Service (PaaS) Deployments

### Option A: Railway / Render (Unified Container)
1. Link your GitHub repository.
2. Create a Web Service pointing to `backend/Dockerfile`.
   - Set environment variables from `.env.example`.
   - Add a persistent disk mounted at `/app/data` and `/app/.cache`.
3. Create a second Web Service pointing to `frontend/Dockerfile`.
   - Set `INTERNAL_API_URL` to the private internal URL of your backend.

### Option B: Hybrid (Vercel Frontend + Render/VPS Backend)
- **Backend**: Deploy `backend/Dockerfile` on Render, Fly.io, or VPS. Set `CORS_ORIGINS=https://your-frontend.vercel.app`.
- **Frontend**: Deploy `frontend/` directly to Vercel. Set `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`.

---

## 4. Environment Variables Reference

| Variable | Default | Description | Required |
|---|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `production`, `testing`) | No |
| `DATABASE_URL` | `sqlite+aiosqlite:///./social_insights.db` | SQLAlchemy async connection string (SQLite or PostgreSQL) | Yes |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed origins (comma-separated, never wildcard in prod) | Yes |
| `INTERNAL_SECRET` | `dev-internal-secret` | Shared secret protecting `/internal/ingest` cron endpoint | Yes |
| `NVIDIA_API_KEY` | `""` | Free tier key for Llama 3.1 8B executive summaries | No (Falls back to Tier 3 templates) |
| `NVIDIA_MODEL` | `meta/llama-3.1-8b-instruct` | LLM model identifier | No |
| `REDDIT_CLIENT_ID` | `""` | Reddit OAuth App Client ID | No |
| `REDDIT_CLIENT_SECRET` | `""` | Reddit OAuth App Secret | No |
| `YOUTUBE_API_KEY` | `""` | Google Cloud API key for YouTube Data API v3 | No |
| `HF_HOME` | `~/.cache/huggingface` | Local cache directory for Twitter-RoBERTa weights | No |
| `SENTENCE_TRANSFORMERS_HOME` | `~/.cache/sbert` | Local cache directory for all-MiniLM-L6-v2 embeddings | No |
| `TORCH_NUM_THREADS` | `2` | Max CPU threads allocated to PyTorch | No |

---

## 5. SSL & Reverse Proxy Setup (Caddy Example)

For automated Let's Encrypt SSL certificates, use Caddy as a front-facing proxy on your server:

```caddyfile
social-insights.example.com {
    # Reverse proxy frontend requests
    reverse_proxy localhost:3000

    # Direct API routes to backend
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /health {
        reverse_proxy localhost:8000
    }
    handle /ready {
        reverse_proxy localhost:8000
    }
}
```

---

## 6. Backups & Disaster Recovery

### Backing up SQLite:
```bash
# Safely snapshot the SQLite database without locking active writers:
sqlite3 social_insights.db ".backup 'social_insights_backup_$(date +%Y%m%d).db'"
```

### Backing up PostgreSQL:
```bash
docker compose exec db pg_dump -U postgres social_insights > backup_$(date +%Y%m%d).sql
```
