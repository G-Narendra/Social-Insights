"""
Pydantic schemas for User authentication, signup, login, and RBAC.
"""

from __future__ import annotations

import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

RoleType = Literal["admin", "analyst", "viewer"]


class UserSignupRequest(BaseModel):
    """Payload for creating a new user account."""

    email: str = Field(..., description="Valid corporate or personal email address")
    password: str = Field(
        ..., min_length=8, description="Strong password with minimum 8 characters"
    )
    full_name: str | None = Field(default=None, max_length=120)
    role: RoleType = Field(default="analyst", description="Account permission role")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Invalid email format. Please provide a valid email address.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters in length.")
        return v


class UserLoginRequest(BaseModel):
    """Payload for authenticating an existing user."""

    email: str = Field(..., description="User account email")
    password: str = Field(..., description="User account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class DemoLoginRequest(BaseModel):
    """Payload for 1-click recruiter/demo role testing."""

    role: RoleType = Field(default="analyst", description="Role to test: admin, analyst, or viewer")


class UserResponse(BaseModel):
    """Public user identity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    full_name: str | None = None
    created_at: datetime.datetime


class TokenResponse(BaseModel):
    """JWT bearer token and authenticated user payload."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
