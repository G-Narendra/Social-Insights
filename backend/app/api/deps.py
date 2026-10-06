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

from app.db.models import User
from app.services.auth_service import get_user_by_id
from app.services.security import decode_access_token

# Simple in-memory sliding-window rate limiter per client IP
_rate_limit_records: dict[str, collections.deque[float]] = collections.defaultdict(
    collections.deque
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an active database session."""
    async for session in get_session():
        yield session


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """
    Validate JWT Bearer token and retrieve authenticated user.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Missing or invalid Bearer authentication token"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    payload = decode_access_token(token, settings.internal_secret)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Authentication token has expired or is invalid"},
        )

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid token subject identifier"},
        )

    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_not_found", "message": "User account not found or deactivated"},
        )

    return user


async def get_optional_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """
    Retrieve user if valid Bearer token is provided; otherwise returns None (for guest/public access).
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization.split("Bearer ", 1)[1].strip()
        payload = decode_access_token(token, settings.internal_secret)
        if not payload or "sub" not in payload:
            return None
        return await get_user_by_id(db, int(payload["sub"]))
    except Exception:
        return None


def require_role(allowed_roles: list[str]):
    """
    Enforce Role-Based Access Control (RBAC).
    Raises HTTP 403 Forbidden if the authenticated user's role is not authorized.
    """

    async def _role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "insufficient_permissions",
                    "message": f"Action requires one of [{', '.join(allowed_roles)}] privileges. Current role: {user.role}",
                },
            )
        return user

    return _role_checker


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
