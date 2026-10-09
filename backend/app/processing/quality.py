"""
Quality filtering and spam heuristic detection.
Validates minimum textual length, language compliance, link density,
and promotional bot spam phrases.
"""

from __future__ import annotations

import re

from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# Enforce deterministic results from langdetect
DetectorFactory.seed = 42

SPAM_PATTERNS = [
    re.compile(r"\b(crypto\s+airdrop|free\s+giveaway|claim\s+free\s+tokens)\b", re.IGNORECASE),
    re.compile(r"\b(subscribe\s+to\s+my\s+onlyfans|follow\s+for\s+follow|f4f)\b", re.IGNORECASE),
    re.compile(r"\b(click\s+here\s+to\s+win|earn\s+\$\d+\s+daily)\b", re.IGNORECASE),
    re.compile(r"\b(whatsapp\s+\+\d{10,}|telegram\s+@\w+)\b", re.IGNORECASE),
    re.compile(r"\b(discount\s+code\s+use\s+\w+|use\s+promo\s+code)\b", re.IGNORECASE),
    re.compile(
        r"\b(affiliate\s+link|amzn\.to/\w+|join\s+telegram|cashapp\s+flip)\b", re.IGNORECASE
    ),
]


def detect_language(text: str) -> str:
    """Detect ISO language code safely."""
    try:
        cleaned = re.sub(r"https?://\S+", "", text)
        cleaned = re.sub(r"\d+", "", cleaned).strip()
        if len(cleaned) < 15:
            return "en"
        return detect(cleaned)
    except LangDetectException:
        return "unknown"


def check_quality(
    text: str,
    min_length: int = 30,
    allowed_languages: list[str] | None = None,
) -> tuple[bool, str | None, str]:
    """
    Check if a mention meets minimum quality thresholds:
    1. Minimum character length (excluding pure URLs)
    2. Spam phrase detection
    3. Link density check (>50% of words are URLs)
    4. Language check (defaults to English 'en')
    Returns (is_quality_passed, drop_reason, detected_language).
    """
    cleaned = text.strip()

    # 1. Minimum useful length
    text_no_urls = re.sub(r"https?://\S+", "", cleaned).strip()
    if len(text_no_urls) < min_length:
        return False, "too_short", "unknown"

    # 2. Promotional spam phrases
    for pattern in SPAM_PATTERNS:
        if pattern.search(cleaned):
            return False, "spam_promo", "en"

    # 3. Excessive link density (e.g. link farm posts)
    words = cleaned.split()
    url_count = len(re.findall(r"https?://\S+", cleaned))
    if len(words) > 0 and (url_count / len(words)) >= 0.5 and len(words) > 3:
        return False, "spam_link_density", "en"

    # 4. Language detection
    lang = detect_language(cleaned)
    allowed = allowed_languages or ["en"]
    if allowed and lang not in allowed and lang != "unknown":
        return False, "non_english", lang

    return True, None, lang
