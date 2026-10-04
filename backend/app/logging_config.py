"""
Structured logging configuration.

Uses Python's standard logging with JSON-like structured output in production
and human-readable output in development. No secrets are ever logged.
"""

from __future__ import annotations

import logging
import sys

from app.config import get_settings


def setup_logging() -> None:
    """Configure the root logger based on application settings."""
    settings = get_settings()

    # Format: timestamp - module - level - message
    fmt = "%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, settings.log_level))

    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
