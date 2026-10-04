"""
Topic Classification Engine (Tier 1).
Uses sentence embeddings (all-MiniLM-L6-v2) compared against 8 topic prototype centroids
combined with deterministic keyword-rule boosts.
Returns primary topic, confidence score, and optional secondary topic.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from app.ml.model_loader import get_embedding_model
from app.processing.normalize import prepare_model_text

logger = logging.getLogger(__name__)

# The 8 fixed system topics
TOPIC_SET = [
    "product",
    "pricing",
    "customer_service",
    "quality",
    "competitors",
    "complaints",
    "features",
    "other",
]

# Rich prototype descriptions defining each topic's semantic centroid
TOPIC_PROTOTYPES = {
    "product": [
        "Vehicle model announcement, specifications, horsepower, torque, dimensions, and styling.",
        "Interior cabin design, cargo space, seats, exterior paint, headlights, and trim levels.",
        "Engine performance, hybrid powertrain, transmission, all-wheel drive, and mechanical specs.",
    ],
    "pricing": [
        "Vehicle price, MSRP, monthly payment, lease options, interest rate, and financing.",
        "Dealership markup above sticker price, market adjustment fees, discounts, and affordability.",
        "Too expensive for the value, overpriced options, high cost of ownership, and budget considerations.",
    ],
    "customer_service": [
        "Dealership customer service experience, sales staff professionalism, and salesperson honesty.",
        "Service department maintenance visit, warranty claims, repair delays, and dealer support.",
        "Unresponsive customer support, long phone hold times, and poor service center treatment.",
    ],
    "quality": [
        "Long term vehicle reliability, durability over 100k miles, build quality, and dependability.",
        "Official safety recall, mechanical breakdown, transmission failure, rust, squeaks, and rattles.",
        "Flawless fit and finish, solid construction, no unexpected repairs, and high consumer reports rating.",
    ],
    "competitors": [
        "Comparison against competing brands like Honda, Ford, Hyundai, Tesla, Subaru, Kia, or Chevrolet.",
        "Why this vehicle is better or worse than alternative rival models in the same segment.",
        "Shoppers cross-shopping competing automakers and deciding between brand options.",
    ],
    "complaints": [
        "Angry customer regrets purchase, awful experience, lemon law claim, and severe frustration.",
        "Repeated broken components, unresolved vehicle flaws, dealer refusing repairs, and class action lawsuit.",
        "Terrible experience from start to finish, completely dissatisfied and warning others not to buy.",
    ],
    "features": [
        "Touchscreen infotainment display, Apple CarPlay, Android Auto, navigation, and bluetooth audio.",
        "Advanced driver assistance systems, adaptive cruise control, lane keep assist, and automated braking.",
        "Fuel economy, real-world MPG, battery range, wireless phone charging, and heated ventilated seats.",
    ],
    "other": [
        "Stock market shares, quarterly corporate earnings call, general financial news, and executive leadership.",
        "Miscellaneous discussion, brief passing reference, unrelated background chatter, and casual mention.",
    ],
}

# Rule boosts for unambiguous lexical indicators
KEYWORD_BOOSTS = {
    "pricing": re.compile(r"\b(price|pricing|msrp|cost|expensive|markup|discount|lease|financing|\$\d+)\b", re.IGNORECASE),
    "quality": re.compile(r"\b(reliable|reliability|durable|durability|recall|breakdown|transmission|squeak|rattle)\b", re.IGNORECASE),
    "customer_service": re.compile(r"\b(dealer|dealership|salesman|sales rep|service department|warranty claim|support agent)\b", re.IGNORECASE),
    "competitors": re.compile(r"\b(honda|ford|hyundai|tesla|kia|subaru|nissan|chevrolet|mazda|competitor|rival)\b", re.IGNORECASE),
    "complaints": re.compile(r"\b(lemon|lawsuit|regret|furious|horrible|terrible|awful|scam|unacceptable)\b", re.IGNORECASE),
    "features": re.compile(r"\b(carplay|android auto|infotainment|mpg|fuel economy|cruise control|heated seats|sound system)\b", re.IGNORECASE),
}

_prototype_centroids: dict[str, np.ndarray] | None = None


def get_prototype_centroids() -> dict[str, np.ndarray]:
    """Precompute and cache normalized embedding centroids for all topics."""
    global _prototype_centroids
    if _prototype_centroids is not None:
        return _prototype_centroids

    model = get_embedding_model()
    centroids: dict[str, np.ndarray] = {}

    for topic, sentences in TOPIC_PROTOTYPES.items():
        embeddings = model.encode(sentences, normalize_embeddings=True)
        centroid = np.mean(embeddings, axis=0)
        # Normalize centroid vector
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        centroids[topic] = centroid

    _prototype_centroids = centroids
    return _prototype_centroids


@dataclass
class TopicResult:
    """Topic classification prediction output."""

    topic: str
    score: float
    secondary_topic: str | None = None
    embedding: list[float] | None = None


def classify_topics_batch(
    texts: list[str],
    confidence_floor: float = 0.22,
) -> list[TopicResult]:
    """
    Classify topics for a batch of texts using centroid cosine similarity + rule boosts.
    """
    if not texts:
        return []

    cleaned = [prepare_model_text(t, max_chars=400) for t in texts]

    try:
        model = get_embedding_model()
        centroids = get_prototype_centroids()
        embeddings = model.encode(cleaned, normalize_embeddings=True)
    except Exception as exc:
        logger.warning("Topic embedding model unavailable (%s). Using rule heuristics.", exc)
        return [_rule_fallback_topic(t) for t in cleaned]

    results: list[TopicResult] = []

    topic_names = list(centroids.keys())
    # Shape: (num_topics, embedding_dim)
    centroid_matrix = np.array([centroids[t] for t in topic_names])

    # Dot product of normalized vectors = cosine similarity. Shape: (num_texts, num_topics)
    similarities = np.dot(embeddings, centroid_matrix.T)

    for i, sim_row in enumerate(similarities):
        text = cleaned[i]
        scores = dict(zip(topic_names, sim_row))

        # Apply keyword rule boosts (+0.12 bonus for explicit lexical markers)
        for topic, pattern in KEYWORD_BOOSTS.items():
            if pattern.search(text):
                scores[topic] = scores.get(topic, 0.0) + 0.12

        # Sort topics by score
        sorted_topics = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_topic, best_score = sorted_topics[0]
        second_topic, second_score = sorted_topics[1]

        # If best score is below minimum floor, classify as 'other'
        if best_score < confidence_floor:
            best_topic = "other"
            best_score = 0.50
            secondary = None
        else:
            # Secondary topic if close to primary and above floor
            secondary = (
                second_topic
                if (second_score >= confidence_floor and (best_score - second_score) < 0.15)
                else None
            )

        emb_list = embeddings[i].tolist() if i < len(embeddings) else None

        results.append(
            TopicResult(
                topic=best_topic,
                score=round(float(best_score), 4),
                secondary_topic=secondary,
                embedding=emb_list,
            )
        )

    return results


def _rule_fallback_topic(text: str) -> TopicResult:
    """Fallback classifier when model is offline."""
    for topic, pattern in KEYWORD_BOOSTS.items():
        if pattern.search(text):
            return TopicResult(topic=topic, score=0.75, secondary_topic=None, embedding=None)
    return TopicResult(topic="other", score=0.50, secondary_topic=None, embedding=None)
