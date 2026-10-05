# ==============================================================================
# Stage 1: Build dependencies in a clean virtual environment
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install compilation essentials for packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create isolated virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build system tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install CPU-optimized PyTorch first into /opt/venv
RUN pip install --no-cache-dir torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu

# Copy dependencies and install completely into /opt/venv
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Minimal runtime image
# ==============================================================================
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Install curl for container HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the complete virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user and persistent directories
RUN groupadd -g 1001 appuser && \
    useradd -u 1001 -g appuser -s /bin/bash -m appuser && \
    mkdir -p /app/data /app/.cache/huggingface /app/.cache/sbert && \
    chown -R appuser:appuser /app

# Copy application source code and migrations configuration
COPY --chown=appuser:appuser app /app/app
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sbert \
    DATABASE_URL=sqlite+aiosqlite:////app/data/social_insights.db \
    APP_ENV=production \
    PORT=8000

# Switch to non-privileged user
USER appuser

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
