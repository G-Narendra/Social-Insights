"""
Unit tests for authentication, password hashing, and HS256 JWT tokens.
"""

from __future__ import annotations

import pytest
from app.services.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import UserSignupRequest, DemoLoginRequest


class TestSecurityUnit:
    def test_password_hash_and_verify(self) -> None:
        raw_password = "SuperSecretPassword123!"
        hashed = hash_password(raw_password)

        assert hashed.startswith("pbkdf2:sha256:100000$")
        assert verify_password(raw_password, hashed) is True
        assert verify_password("WrongPassword123!", hashed) is False

    def test_jwt_create_and_decode(self) -> None:
        secret = "test-secret-key-for-jwt-signing"
        payload = {"sub": "42", "email": "test@domain.com", "role": "admin"}
        token = create_access_token(payload, secret, expires_delta_seconds=3600)

        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

        decoded = decode_access_token(token, secret)
        assert decoded is not None
        assert decoded["sub"] == "42"
        assert decoded["email"] == "test@domain.com"
        assert decoded["role"] == "admin"

    def test_jwt_tamper_rejected(self) -> None:
        secret = "test-secret-key-for-jwt-signing"
        token = create_access_token({"sub": "1"}, secret)
        tampered = token[:-4] + "abcd"

        assert decode_access_token(tampered, secret) is None
        assert decode_access_token(token, "wrong-secret-key") is None

    def test_signup_validation(self) -> None:
        valid = UserSignupRequest(email="valid.user@company.com", password="Password123!")
        assert valid.email == "valid.user@company.com"

        with pytest.raises(ValueError, match="Invalid email format"):
            UserSignupRequest(email="not-an-email", password="Password123!")

        with pytest.raises(ValueError, match="at least 8 characters"):
            UserSignupRequest(email="valid@company.com", password="short")
