"""
FastAPI application factory and startup.
Wires routers, CORS, structured logging, consistent error formatting, and health checks.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

import asyncio

from app.api import (
    alerts,
    auth,
    collect,
    compare,
    insights,
    internal,
    keywords,
    mentions,
    stats,
)
from app.config import get_settings
from app.db.session import close_db, get_session_factory, init_db
from app.logging_config import setup_logging
from app.ml.model_loader import get_embedding_model, get_sentiment_pipeline
from app.ml.topics import get_prototype_centroids
from app.services.auth_service import seed_default_users

logger = logging.getLogger(__name__)


async def _warmup_ml_models() -> None:
    """Pre-warm ML models in background worker thread pool so first collection runs instantly."""
    settings = get_settings()
    if settings.low_memory_mode:
        logger.info("Low memory mode enabled: Skipping heavy ML model pre-warming.")
        return

    try:
        logger.info("Pre-warming ML models in background worker thread...")
        await asyncio.to_thread(get_sentiment_pipeline)
        await asyncio.to_thread(get_embedding_model)
        await asyncio.to_thread(get_prototype_centroids)
        logger.info("ML models successfully pre-warmed.")
    except Exception as exc:
        logger.warning("ML model pre-warmup deferred (%s)", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown tasks."""
    setup_logging()
    settings = get_settings()
    logger.info("Starting Social Insights API (env=%s)", settings.app_env)

    # Initialize database tables
    await init_db()
    logger.info("Database initialized")

    # Seed default RBAC users
    try:
        factory = get_session_factory()
        async with factory() as session:
            await seed_default_users(session)
        logger.info("Default RBAC accounts initialized")
    except Exception as exc:
        logger.warning("Auto-seed users deferred (%s)", exc)

    # Start non-blocking background model pre-warming if not in low memory mode
    if not settings.low_memory_mode:
        asyncio.create_task(_warmup_ml_models())

    yield

    logger.info("Shutting down Social Insights API")
    await close_db()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Social Insights API",
        description="Open-source social listening platform with tiered AI intelligence",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — allow explicit list plus standard Vercel and Render deployments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # HTTPException handler — consistent {error: {code, message}} format
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code = "error"
        message = str(exc.detail)
        if isinstance(exc.detail, dict):
            code = exc.detail.get("code", "error")
            message = exc.detail.get("message", str(exc.detail))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message}},
        )

    # Validation error handler — consistent format for invalid client input (HTTP 422)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = exc.errors()
        err_msg = details[0].get("msg") if details else "Invalid request data"
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": err_msg}},
        )

    # Global unhandled exception handler — never leak stack traces
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "internal_error", "message": "An unexpected error occurred"}
            },
        )

    # Root endpoint
    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        """Root endpoint returning service identity and health links."""
        return {
            "status": "ok",
            "service": "Social Insights API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    # Liveness health check
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Basic liveness check."""
        return {"status": "ok"}

    # Readiness check — verifies database connectivity
    @app.get("/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        """Readiness check — verifies DB connectivity."""
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "ready"}
        except Exception as exc:
            logger.error("Readiness check failed: %s", exc)
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "Database connection failed"},
            )

    # Mount API routers
    app.include_router(auth.router)
    app.include_router(collect.router)
    app.include_router(keywords.router)
    app.include_router(mentions.router)
    app.include_router(stats.router)
    app.include_router(insights.router)
    app.include_router(compare.router)
    app.include_router(alerts.router)
    app.include_router(internal.router)

    return app


app = create_app()
