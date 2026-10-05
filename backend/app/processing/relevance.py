"""
Relevance filtering and brand disambiguation.
Enforces word-boundary keyword matching, URL-only keyword exclusion,
and context-hint semantic checks for ambiguous brand names (e.g. Apple, Meta, Mercury).
"""

from __future__ import annotations

import re

# Domain associations for high-profile ambiguous terms to prevent false drops
DOMAIN_ASSOCIATIONS: dict[str, set[str]] = {
    "apple": {
        "iphone",
        "ipad",
        "mac",
        "macbook",
        "ios",
        "macos",
        "app store",
        "tim cook",
        "airpods",
        "apple watch",
        "silicon",
        "m1",
        "m2",
        "m3",
        "m4",
        "technology",
        "tech",
        "device",
        "gadget",
        "hardware",
        "software",
        "cupertino",
    },
    "meta": {
        "facebook",
        "instagram",
        "whatsapp",
        "zuckerberg",
        "oculus",
        "quest",
        "threads",
        "llama",
        "metaverse",
        "social media",
        "ad revenue",
        "vr",
        "ai",
    },
    "target": {
        "store",
        "retail",
        "shopping",
        "cart",
        "discount",
        "merchandise",
        "redcard",
        "groceries",
        "supermarket",
        "retailer",
    },
    "amazon": {
        "aws",
        "prime",
        "bezos",
        "ecommerce",
        "alexa",
        "kindle",
        "delivery",
        "warehouse",
        "marketplace",
        "cloud",
    },
    "mercury": {
        "car",
        "marine",
        "outboard",
        "motor",
        "cougar",
        "sable",
        "ford",
        "boat",
        "engine",
    },
}

AMBIGUOUS_TERMS = set(DOMAIN_ASSOCIATIONS.keys()) | {
    "oracle",
    "square",
    "block",
    "uber",
    "alphabet",
}


def _phrase_to_regex_pattern(phrase: str) -> str:
    """Convert a phrase into a pattern with flexible whitespace and hyphen delimiters."""
    parts = [re.escape(p) for p in re.split(r"[-\s]+", phrase.strip()) if p]
    if not parts:
        return ""
    return r"[-\s]+".join(parts)


def build_keyword_regex(keyword: str, aliases: list[str] | None = None) -> re.Pattern:
    """Build a compiled word-boundary regular expression for keyword and all aliases."""
    raw_terms = [keyword.strip()]
    if aliases:
        for alias in aliases:
            cleaned = alias.strip()
            if cleaned:
                raw_terms.append(cleaned)

    pattern_parts = []
    for term in raw_terms:
        sub = _phrase_to_regex_pattern(term)
        if sub:
            pattern_parts.append(sub)

    pattern_str = r"\b(?:" + "|".join(pattern_parts) + r")\b"
    return re.compile(pattern_str, re.IGNORECASE)


def is_keyword_only_in_url(raw_text: str, keyword_pattern: re.Pattern) -> bool:
    """
    Check if the keyword appears strictly within a URL string rather than actual discussion text.
    """
    if not re.search(r"https?://\S+", raw_text):
        return False
    if not keyword_pattern.search(raw_text):
        return False
    no_urls = re.sub(r"https?://\S+", "", raw_text)
    return not bool(keyword_pattern.search(no_urls))


def check_relevance(
    text: str,
    title: str | None,
    keyword: str,
    aliases: list[str] | None = None,
    context_hint: str | None = None,
) -> tuple[bool, str | None]:
    """
    Evaluate if a mention is relevant to the target keyword:
    1. Must match keyword or alias on word boundaries (flexible whitespace/hyphen)
    2. Multi-word phrases (>= 3 words) allow high-confidence token overlap (>= 65%)
    3. Must not be present exclusively in a URL
    4. If keyword is ambiguous, verify presence of context hint or domain association terms
    Returns (is_relevant, drop_reason).
    """
    combined_text = f"{title or ''} {text}".strip()
    if not combined_text:
        return False, "irrelevant_empty"

    pattern = build_keyword_regex(keyword, aliases)
    match = pattern.search(combined_text)

    # For multi-word queries with 3+ significant tokens, allow high token overlap
    if not match:
        tokens = [
            w.lower()
            for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", keyword)
            if w.lower() not in {"the", "and", "for", "with", "from", "that", "this", "about"}
        ]
        if len(tokens) >= 3:
            text_lower = combined_text.lower()
            matched_tokens = sum(
                1 for tok in tokens if re.search(r"\b" + re.escape(tok) + r"\b", text_lower)
            )
            if (matched_tokens / len(tokens)) >= 0.65:
                match = True

    if not match:
        return False, "irrelevant_keyword"

    # Check if keyword only appears inside a URL
    if is_keyword_only_in_url(combined_text, pattern):
        return False, "irrelevant_url_only"

    # Ambiguity handling
    norm_kw = keyword.lower().strip()
    if norm_kw in AMBIGUOUS_TERMS and context_hint:
        hint_terms = set(re.findall(r"\b[a-zA-Z]{3,}\b", context_hint.lower()))
        # Supplement with known domain associations
        domain_terms = DOMAIN_ASSOCIATIONS.get(norm_kw, set())
        valid_terms = hint_terms | domain_terms

        if valid_terms:
            text_lower = combined_text.lower()
            has_context = any(term in text_lower for term in valid_terms)
            if not has_context:
                return False, "irrelevant_ambiguous"

    return True, None
