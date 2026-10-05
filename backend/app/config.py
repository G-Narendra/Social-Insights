"""
Application configuration loaded from environment variables.

Uses pydantic-settings for type-safe config with validation at startup.
All secrets and tuneable parameters are loaded here and nowhere else.
Fails loudly on missing required values so misconfiguration is caught early.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Safe model cache initialization
hf_cache = os.environ.get("HF_HOME")
if not hf_cache or hf_cache.startswith("/.cache"):
    hf_cache = "/tmp/huggingface"
sbert_cache = os.environ.get("SENTENCE_TRANSFORMERS_HOME")
if not sbert_cache or sbert_cache.startswith("/.cache"):
    sbert_cache = "/tmp/sbert"

os.environ.setdefault("HF_HOME", hf_cache)
os.environ.setdefault("TRANSFORMERS_CACHE", hf_cache)
os.environ.setdefault("SENTENCE_TRANSFORMERS_HOME", sbert_cache)


class Settings(BaseSettings):
    """Central configuration - every tuneable knob lives here."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    log_level: str = "INFO"
    internal_secret: str = "change-me-to-a-random-secret"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./social_insights.db"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    # --- Reddit (optional) ---
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    reddit_user_agent: str = "SocialInsights/1.0"

    # --- YouTube (optional) ---
    youtube_api_key: str | None = None

    # --- NVIDIA NIM LLM (optional) ---
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.2-11b-vision-instruct"

    # --- AI/ML tuning ---
    low_memory_mode: bool = True
    llm_max_items_per_run: int = 20
    confidence_threshold: float = 0.6
    dedup_similarity_threshold: float = 0.92
    min_text_length: int = 30

    # --- Rate limiting ---
    collect_rate_limit: str = "5/minute"
    refresh_rate_limit: str = "3/minute"

    # --- Computed properties ---
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_available(self) -> bool:
        return bool(self.nvidia_api_key)

    @property
    def reddit_available(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)

    @property
    def youtube_available(self) -> bool:
        return bool(self.youtube_api_key)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://") :]
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got '{v}'")
        return upper


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings instance. Cached after first call."""
    return Settings()
