"""
Sentiment Analysis Engine (Tier 1).
Uses CardiffNLP's Twitter-RoBERTa 3-class sentiment model.
Executes batched CPU inference with softmax confidence scores and low-confidence gating.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence

from app.ml.model_loader import get_sentiment_pipeline
from app.processing.normalize import prepare_model_text

logger = logging.getLogger(__name__)

# Label mapping for twitter-roberta-base-sentiment-latest
LABEL_MAP = {
    "positive": "positive",
    "neutral": "neutral",
    "negative": "negative",
    "label_0": "negative",
    "label_1": "neutral",
    "label_2": "positive",
}


@dataclass
class SentimentResult:
    """Prediction outcome for a single text."""

    label: str  # positive, neutral, negative
    score: float  # confidence score [0.0 - 1.0]
    is_low_confidence: bool  # True if below gating threshold


def analyze_sentiment_batch(
    texts: list[str],
    batch_size: int = 32,
    confidence_threshold: float = 0.55,
) -> list[SentimentResult]:
    """
    Run batched sentiment analysis over an array of texts.
    Returns SentimentResult with label, confidence score, and low_confidence flag.
    """
    if not texts:
        return []

    # Clean and format texts for model consumption
    cleaned_texts = [prepare_model_text(t, max_chars=500) for t in texts]

    try:
        classifier = get_sentiment_pipeline()
        outputs = classifier(cleaned_texts, batch_size=batch_size)
    except Exception as exc:
        logger.warning("Sentiment model unavailable or failed (%s). Falling back to rule heuristics.", exc)
        return [_rule_fallback_sentiment(t) for t in cleaned_texts]

    results: list[SentimentResult] = []

    for item_scores in outputs:
        # item_scores is a list of dicts: [{'label': 'positive', 'score': 0.85}, ...]
        if not item_scores:
            results.append(SentimentResult("neutral", 0.5, True))
            continue

        best = max(item_scores, key=lambda x: x["score"])
        raw_label = best["label"].lower()
        normalized_label = LABEL_MAP.get(raw_label, "neutral")
        confidence = float(best["score"])

        is_low = confidence < confidence_threshold
        results.append(SentimentResult(normalized_label, round(confidence, 4), is_low))

    return results


def _rule_fallback_sentiment(text: str) -> SentimentResult:
    """Fast lexical fallback when model is unavailable or in minimal offline test modes."""
    t_lower = text.lower()
    pos_words = {"love", "great", "excellent", "amazing", "good", "reliable", "best", "perfect", "fantastic"}
    neg_words = {"hate", "awful", "terrible", "bad", "broken", "issue", "problem", "expensive", "fail", "markup", "recall"}

    pos_hits = sum(1 for w in pos_words if w in t_lower)
    neg_hits = sum(1 for w in neg_words if w in t_lower)

    if pos_hits > neg_hits:
        return SentimentResult("positive", 0.75, False)
    elif neg_hits > pos_hits:
        return SentimentResult("negative", 0.75, False)
    return SentimentResult("neutral", 0.60, False)
