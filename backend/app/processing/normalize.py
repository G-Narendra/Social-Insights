"""
Text normalization and tokenization for social listening.
Applies Unicode NFKC normalization, HTML entity stripping,
character repeat collapsing, and model token replacements while preserving
original emojis and raw text for UI display.
"""

from __future__ import annotations

import html
import re
import unicodedata

from bs4 import BeautifulSoup

# Regex to detect URLs
URL_PATTERN = re.compile(
    r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)

# Regex to detect social handles (@username)
MENTION_PATTERN = re.compile(r"(?<=^|(?<=[^a-zA-Z0-9_]))@([A-Za-z0-9_]{1,30})")

# Regex for excessive character repeats (e.g. "sooooo" -> "soo", letters only to preserve numbers like 111 or 777)
REPEAT_CHAR_PATTERN = re.compile(r"([a-zA-Z])\1{2,}")
REPEAT_PUNCT_PATTERN = re.compile(r"([!?.]){2,}")

# Whitespace collapsing
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_html(text: str) -> str:
    """Strip HTML tags and decode HTML entities safely."""
    if not text:
        return ""
    # Quick check if text contains HTML tag characters
    if "<" in text and ">" in text:
        try:
            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(separator=" ")
        except Exception:
            # Fallback to regex stripping
            text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(text)


def normalize_text(text: str) -> str:
    """
    Standardize text into canonical form:
    1. Unicode NFKC normalization
    2. Strip HTML tags & unescape entities
    3. Collapse character repeats (e.g. "sooooo" -> "soo")
    4. Collapse whitespace and trim
    """
    if not text:
        return ""

    # 1. Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # 2. HTML stripping & unescape
    normalized = clean_html(normalized)

    # 3. Collapse excessive character repetition (3+ of same char to 2)
    normalized = REPEAT_CHAR_PATTERN.sub(r"\1\1", normalized)

    # 4. Collapse punctuation repeats (e.g. "????" -> "??")
    normalized = REPEAT_PUNCT_PATTERN.sub(r"\1\1", normalized)

    # 5. Collapse whitespace and strip
    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()

    return normalized


def prepare_model_text(text: str, max_chars: int = 1000) -> str:
    """
    Prepares normalized text specifically for NLP classification models:
    - Replaces URLs with <url>
    - Replaces user mentions with <user>
    - Truncates extreme length preserving head and tail
    """
    if not text:
        return ""

    # Replace URLs and user handles with special tokens
    model_text = URL_PATTERN.sub("<url>", text)
    model_text = MENTION_PATTERN.sub("<user>", model_text)
    model_text = WHITESPACE_PATTERN.sub(" ", model_text).strip()

    # If text is extremely long, retain first 60% and last 40% up to max_chars
    if len(model_text) > max_chars:
        head_len = int(max_chars * 0.6)
        tail_len = int(max_chars * 0.4)
        model_text = f"{model_text[:head_len]} ... {model_text[-tail_len:]}"

    return model_text
