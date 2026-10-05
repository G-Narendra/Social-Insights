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
        "Vehicle model announcement, tech product launch, hardware specifications, and design styling.",
        "Software platform, artificial intelligence model, mobile app, gadget release, or creative project.",
        "Powertrain, engine performance, system architecture, device build, and product releases.",
    ],
    "pricing": [
        "Product price, vehicle MSRP, subscription tier, billing, lease options, and affordability.",
        "Executive compensation, net worth, company valuation, stock market capitalization, and financing.",
        "Overpriced goods, expensive options, hidden fees, budget constraints, and cost of ownership.",
    ],
    "customer_service": [
        "Customer service responsiveness, support desk professionalism, and client satisfaction.",
        "Public relations communication, official press statements, warranty claims, and user support.",
        "Unresponsive support representatives, long wait times, and poor service experience.",
    ],
    "quality": [
        "Long-term reliability, build durability, flawless craftsmanship, and proven track record.",
        "Official safety recall, product defects, system outages, personal credibility, and reputation.",
        "Solid construction, engineering excellence, high consumer ratings, and dependable execution.",
    ],
    "competitors": [
        "Comparison against competing brands, industry rivals, alternative peers, and market contenders.",
        "Why this product or leader is better or worse than market alternatives in the same segment.",
        "Cross-shopping different solutions, market share competition, and head-to-head comparisons.",
    ],
    "complaints": [
        "Dissatisfied customer reviews, severe frustration, public controversy, and consumer regret.",
        "Public backlash, executive criticism, lawsuits, broken promises, ethical concerns, and boycott calls.",
        "Terrible experience, unresolved defects, severe criticism, and warnings to avoid.",
    ],
    "features": [
        "Product features, technical capabilities, software updates, advanced tools, and innovations.",
        "Key specifications, algorithmic breakthroughs, cutting-edge functionality, and performance metrics.",
        "New release features, battery range, user interface options, and patent announcements.",
    ],
    "other": [
        "Quarterly corporate earnings, general biographical news, interviews, and public appearances.",
        "Miscellaneous discussion, passing references, casual background chatter, and general commentary.",
    ],
}

# Rule boosts for unambiguous lexical indicators
KEYWORD_BOOSTS = {
    "pricing": re.compile(
        r"\b(price|pricing|msrp|cost|expensive|markup|discount|lease|financing|\$\d+|salary|compensation|net worth|valuation|billion|million)\b",
        re.IGNORECASE,
    ),
    "quality": re.compile(
        r"\b(reliable|reliability|durable|durability|recall|breakdown|transmission|reputation|credibility|integrity|track record|craftsmanship)\b",
        re.IGNORECASE,
    ),
    "customer_service": re.compile(
        r"\b(dealer|dealership|salesman|sales rep|service department|warranty claim|support agent|customer support|client service|public relations|press office)\b",
        re.IGNORECASE,
    ),
    "competitors": re.compile(
        r"\b(honda|ford|hyundai|tesla|kia|subaru|nissan|chevrolet|mazda|apple|google|microsoft|competitor|rival|versus|vs\.?|alternative|peer|contender|outperformed)\b",
        re.IGNORECASE,
    ),
    "complaints": re.compile(
        r"\b(lemon|lawsuit|regret|furious|horrible|terrible|awful|scam|unacceptable|backlash|scandal|controversy|criticism|dispute|boycott)\b",
        re.IGNORECASE,
    ),
    "features": re.compile(
        r"\b(carplay|android auto|infotainment|mpg|fuel economy|cruise control|heated seats|sound system|feature|features|specs|specification|capability|capabilities|update|innovation)\b",
        re.IGNORECASE,
    ),
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
        scores = dict(zip(topic_names, sim_row, strict=False))

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
