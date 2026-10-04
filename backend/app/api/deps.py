"""
FastAPI dependency injection utilities.
Provides database sessions, secret header authentication for internal endpoints,
and per-IP sliding window rate limiting.
"""

from __future__ import annotations

import collections
import time
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_session

# Simple in-memory sliding-window rate limiter per client IP
_rate_limit_records: dict[str, collections.deque[float]] = collections.defaultdict(
    collections.deque
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an active database session."""
    async for session in get_session():
        yield session


def verify_internal_secret(
    x_internal_secret: str | None = Header(default=None, alias="X-Internal-Secret"),
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Authenticate internal background / scheduler endpoints.
    Requires X-Internal-Secret matching system configuration.
    """
    if not x_internal_secret or x_internal_secret != settings.internal_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "unauthorized", "message": "Invalid or missing internal secret header"},
        )


def enforce_rate_limit(
    max_requests: int = 15,
    window_seconds: int = 60,
):
    """
    Factory creating a per-IP sliding-window rate limiter dependency.
    """

    async def _rate_limiter(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = _rate_limit_records[client_ip]

        # Evict timestamps older than sliding window
        while timestamps and timestamps[0] < now - window_seconds:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: maximum {max_requests} requests per {window_seconds}s.",
                },
            )

        timestamps.append(now)

    return _rate_limiter
