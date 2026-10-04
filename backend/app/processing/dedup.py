"""
Deduplication engine.
Implements exact content hashing (xxhash / sha256), canonical URL deduplication,
and near-duplicate detection using token n-gram Jaccard similarity.
"""

from __future__ import annotations

import hashlib
import re

try:
    import xxhash

    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False


def compute_content_hash(text: str) -> str:
    """
    Compute a fast, deterministic 64-bit content hash of normalized text.
    Uses xxHash64 if available, falling back to SHA-256 truncated to 16 hex chars.
    """
    cleaned = text.lower().strip()
    # Strip whitespace differences
    compact = re.sub(r"\s+", " ", cleaned)

    if HAS_XXHASH:
        return xxhash.xxh64(compact.encode("utf-8")).hexdigest()
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()[:16]


def get_token_shingles(text: str, n: int = 3) -> set[str]:
    """Extract character n-grams or word shingles for near-duplicate comparison."""
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def calculate_jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute Jaccard index between two shingle sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    if union == 0:
        return 0.0
    return intersection / union


class Deduplicator:
    """
    Manages in-memory state for exact hash, canonical URL,
    and near-duplicate detection across a collection run.
    """

    def __init__(self, near_dedup_threshold: float = 0.85) -> None:
        self.seen_hashes: set[str] = set()
        self.seen_urls: set[str] = set()
        self.near_dedup_threshold = near_dedup_threshold
        # Stores (mention_id, shingles)
        self.seen_shingles: list[tuple[str, set[str]]] = []

    def check_duplicate(
        self,
        content_hash: str,
        canonical_url: str | None,
        text: str,
        mention_id: str,
    ) -> tuple[bool, str | None]:
        """
        Check if a mention is an exact or near duplicate.
        Returns (is_duplicate, drop_reason).
        """
        # 1. Exact content hash match
        if content_hash in self.seen_hashes:
            return True, "duplicate_hash"

        # 2. Canonical URL match
        if canonical_url and canonical_url in self.seen_urls:
            return True, "duplicate_url"

        # 3. Near-duplicate check for non-trivial text length
        shingles = get_token_shingles(text, n=3)
        if len(shingles) >= 5:
            for _seen_id, seen_shing in self.seen_shingles:
                sim = calculate_jaccard_similarity(shingles, seen_shing)
                if sim >= self.near_dedup_threshold:
                    return True, "duplicate_near"

        # Mark as seen
        self.seen_hashes.add(content_hash)
        if canonical_url:
            self.seen_urls.add(canonical_url)
        if len(shingles) >= 5:
            self.seen_shingles.append((mention_id, shingles))

        return False, None
