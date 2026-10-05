"""Tests for configuration loading and validation."""

from __future__ import annotations

import pytest

from app.config import Settings


class TestSettings:
    """Verify the settings module handles all cases correctly."""

    def test_defaults_are_sensible(self) -> None:
        """Settings should load with sensible defaults and no env vars."""
        settings = Settings()
        assert settings.app_env == "development"
        assert settings.log_level == "INFO"
        assert "sqlite" in settings.database_url

    def test_cors_origin_list_splits_correctly(self) -> None:
        """CORS origins string should split into a clean list."""
        settings = Settings(cors_origins="http://a.com, http://b.com ,http://c.com")
        assert settings.cors_origin_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_low_memory_mode_default(self) -> None:
        """Low memory mode defaults to True for lightweight container operations."""
        settings = Settings()
        assert settings.low_memory_mode is True

    def test_invalid_log_level_rejected(self) -> None:
        """Invalid log levels should fail validation at startup."""
        with pytest.raises(ValueError, match="log_level must be one of"):
            Settings(log_level="VERBOSE")

    def test_llm_not_available_without_key(self) -> None:
        """LLM should report unavailable when NVIDIA key is missing."""
        settings = Settings(nvidia_api_key=None)
        assert settings.llm_available is False

    def test_llm_available_with_key(self) -> None:
        """LLM should report available when NVIDIA key is set."""
        settings = Settings(nvidia_api_key="nvapi-test-key")
        assert settings.llm_available is True

    def test_reddit_not_available_without_both_keys(self) -> None:
        """Reddit connector needs both client ID and secret."""
        settings = Settings(reddit_client_id="id", reddit_client_secret=None)
        assert settings.reddit_available is False

    def test_youtube_not_available_without_key(self) -> None:
        """YouTube connector needs an API key."""
        settings = Settings(youtube_api_key=None)
        assert settings.youtube_available is False

    def test_database_url_normalization(self) -> None:
        """Verify postgres:// and postgresql:// are normalized to postgresql+asyncpg://."""
        s1 = Settings(database_url="postgres://user:pass@localhost:5432/db")
        assert s1.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"

        s2 = Settings(database_url="postgresql://user:pass@localhost:5432/db")
        assert s2.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"

    def test_normalize_database_connection_sslmode_handling(self) -> None:
        """Verify sslmode=require query param is stripped and mapped to connect_args['ssl'] = 'require'."""
        from app.db.session import normalize_database_connection

        clean_url, connect_args = normalize_database_connection(
            "postgresql+asyncpg://user:pass@ep-test.neon.tech/social_insights?sslmode=require"
        )
        assert "sslmode" not in clean_url
        assert clean_url == "postgresql+asyncpg://user:pass@ep-test.neon.tech/social_insights"
        assert connect_args == {"ssl": "require"}

        # Neon URL with channel_binding and sslmode
        neon_url, neon_args = normalize_database_connection(
            "postgresql://user:pass@ep-test.neon.tech/social_insights?sslmode=require&channel_binding=require"
        )
        assert "channel_binding" not in neon_url
        assert "sslmode" not in neon_url
        assert neon_url == "postgresql+asyncpg://user:pass@ep-test.neon.tech/social_insights"
        assert neon_args == {"ssl": "require"}

        # SQLite check
        sqlite_url, sqlite_args = normalize_database_connection("sqlite+aiosqlite:///./test.db")
        assert sqlite_url == "sqlite+aiosqlite:///./test.db"
        assert sqlite_args == {"check_same_thread": False}

