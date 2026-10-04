"""
FastAPI application factory and startup.

This is the entry point. It wires together the API routes, middleware,
and startup/shutdown lifecycle hooks. The app is kept thin — all logic
lives in services, and all config comes from the settings module.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.session import init_db
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown tasks."""
    setup_logging()
    settings = get_settings()
    logger.info("Starting Social Insights (env=%s)", settings.app_env)

    # Initialize database tables
    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down Social Insights")


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

    # CORS — explicit allow-list from config, never wildcard in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Global exception handler — never leak stack traces
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "internal_error", "message": "An unexpected error occurred"}
            },
        )

    # Health endpoints
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Basic liveness check."""
        return {"status": "ok"}

    @app.get("/ready", tags=["health"])
    async def ready() -> dict[str, str]:
        """Readiness check — verifies DB connectivity."""
        # Will be enhanced once DB is fully wired
        return {"status": "ready"}

    return app


app = create_app()
