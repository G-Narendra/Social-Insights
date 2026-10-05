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


def _stem_word(word: str) -> str:
    """Lightweight suffix stripping for lexical matching (e.g. planting -> plant, trees -> tree)."""
    w = word.lower().strip()
    for suffix in ("ing", "ed", "es", "s"):
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[:-len(suffix)]
    return w


def _matches_multi_word_overlap(combined_text: str, candidate: str, primary_kw: str) -> bool:
    """
    Check if a candidate term has high-confidence stemmed token overlap with text.
    Enforces geographic/brand entity anchors when specified.
    """
    text_lower = combined_text.lower()
    text_norm = re.sub(r"\b(\d+)m\b", r"\1 million \1m", text_lower)
    cand_norm = re.sub(r"\b(\d+)m\b", r"\1 million \1m", candidate.lower())
    prim_norm = re.sub(r"\b(\d+)m\b", r"\1 million \1m", primary_kw.lower())

    # If primary keyword specifies an explicit geographic entity, ensure text aligns
    geo_anchors = ("uae", "emirates", "abu dhabi", "dubai", "sharjah")
    if any(loc in prim_norm for loc in geo_anchors):
        if not any(loc in text_norm for loc in geo_anchors):
            return False

    tokens = [
        w
        for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", cand_norm)
        if w not in {"the", "and", "for", "with", "from", "that", "this", "about"}
    ]
    if len(tokens) < 2:
        return False

    stems = [_stem_word(t) for t in tokens]
    text_tokens = [_stem_word(t) for t in re.findall(r"\b[a-zA-Z0-9]{3,}\b", text_norm)]

    matched = sum(1 for s in stems if s in text_tokens)
    ratio = matched / len(stems)
    threshold = 1.0 if len(stems) == 2 else 0.55
    return ratio >= threshold


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
    2. Multi-word phrases allow stemmed token overlap with entity preservation
    3. Must not be present exclusively in a URL
    4. If keyword is ambiguous, verify presence of context hint or domain association terms
    Returns (is_relevant, drop_reason).
    """
    combined_text = f"{title or ''} {text}".strip()
    if not combined_text:
        return False, "irrelevant_empty"

    pattern = build_keyword_regex(keyword, aliases)
    match = pattern.search(combined_text)

    # For multi-word queries or aliases, check high-confidence stemmed token overlap
    if not match:
        candidates = [keyword] + (aliases or [])
        match = any(_matches_multi_word_overlap(combined_text, cand, keyword) for cand in candidates)

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
