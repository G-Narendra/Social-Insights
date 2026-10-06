"""
User authentication and RBAC service.
Manages user lifecycle, demo seed provisioning, and credential verification.
"""

from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.auth import UserSignupRequest
from app.services.security import (
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

DEMO_ACCOUNTS = [
    {
        "email": "admin@socialinsights.io",
        "password": "Admin@1234",
        "role": "admin",
        "full_name": "System Administrator",
    },
    {
        "email": "analyst@socialinsights.io",
        "password": "Analyst@1234",
        "role": "analyst",
        "full_name": "Lead Market Analyst",
    },
    {
        "email": "viewer@socialinsights.io",
        "password": "Viewer@1234",
        "role": "viewer",
        "full_name": "Executive Stakeholder",
    },
]


async def seed_default_users(db: AsyncSession) -> None:
    """Idempotently seed standard demo users for each RBAC tier."""
    for demo in DEMO_ACCOUNTS:
        stmt = select(User).where(User.email == demo["email"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if not existing:
            user = User(
                email=demo["email"],
                hashed_password=hash_password(demo["password"]),
                role=demo["role"],
                full_name=demo["full_name"],
                is_active=True,
            )
            db.add(user)
            await db.commit()
            logger.info("Provisioned default account: %s (%s)", demo["email"], demo["role"])


async def register_user(
    db: AsyncSession,
    data: UserSignupRequest,
    secret_key: str,
) -> tuple[User, str]:
    """Register a new user and generate access token."""
    # Check if email is already registered
    stmt = select(User).where(User.email == data.email)
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise ValueError("An account with this email address already exists.")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
        full_name=data.full_name or data.email.split("@")[0].title(),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        secret_key=secret_key,
    )
    return user, token


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
    secret_key: str,
) -> tuple[User, str]:
    """Verify credentials and issue JWT access token."""
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("Invalid email or password.")

    if not user.is_active:
        raise ValueError("Account is deactivated.")

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        secret_key=secret_key,
    )
    return user, token


async def get_demo_user_token(
    db: AsyncSession,
    role: str,
    secret_key: str,
) -> tuple[User, str]:
    """Retrieve demo account for the specified role and generate an instant access token."""
    demo_email = f"{role}@socialinsights.io"
    stmt = select(User).where(User.email == demo_email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        # If not yet seeded, provision now
        user = User(
            email=demo_email,
            hashed_password=hash_password(f"{role.capitalize()}@1234"),
            role=role,
            full_name=f"Demo {role.capitalize()}",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role},
        secret_key=secret_key,
    )
    return user, token


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Lookup user by primary key ID."""
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
