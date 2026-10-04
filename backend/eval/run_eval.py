"""
Evaluation runner for Tier 1 Sentiment and Topic Classification models.
Computes accuracy, precision, recall, macro F1, confusion matrices,
and inference latency benchmarks over the 100-sample hand-labeled benchmark.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.sentiment import analyze_sentiment_batch
from app.ml.topics import TOPIC_SET, classify_topics_batch

DATASET_PATH = Path(__file__).parent / "labelled_sample.jsonl"
RESULTS_PATH = Path(__file__).parent / "eval_results.json"


def compute_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
) -> dict[str, float]:
    """Calculate overall accuracy, macro precision, recall, and macro F1."""
    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == yp)
    accuracy = correct / total if total > 0 else 0.0

    precisions = []
    recalls = []
    f1s = []

    for label in labels:
        tp = sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == label and yp == label)
        fp = sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt != label and yp == label)
        fn = sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == label and yp != label)

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0

        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(sum(precisions) / len(precisions), 4),
        "macro_recall": round(sum(recalls) / len(recalls), 4),
        "macro_f1": round(sum(f1s) / len(f1s), 4),
    }


def compute_confusion_matrix(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
) -> dict[str, dict[str, int]]:
    """Build a confusion matrix dictionary."""
    matrix = {actual: {pred: 0 for pred in labels} for actual in labels}
    for yt, yp in zip(y_true, y_pred, strict=False):
        if yt in matrix and yp in matrix[yt]:
            matrix[yt][yp] += 1
    return matrix


def run_evaluation() -> dict:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    # Load dataset
    samples = []
    with open(DATASET_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))

    texts = [s["text"] for s in samples]
    true_sentiments = [s["sentiment"] for s in samples]
    true_topics = [s["topic"] for s in samples]

    print(f"Loaded {len(samples)} evaluation samples.")
    print("=" * 60)

    # 1. Evaluate Sentiment Analysis
    print("Running Sentiment Analysis (Twitter-RoBERTa)...")
    start_t = time.perf_counter()
    sentiment_results = analyze_sentiment_batch(texts, batch_size=32)
    sentiment_duration = time.perf_counter() - start_t
    pred_sentiments = [r.label for r in sentiment_results]
    sentiment_throughput = len(texts) / sentiment_duration if sentiment_duration > 0 else 0.0

    sentiment_labels = ["positive", "neutral", "negative"]
    sentiment_metrics = compute_metrics(true_sentiments, pred_sentiments, sentiment_labels)
    sentiment_cm = compute_confusion_matrix(true_sentiments, pred_sentiments, sentiment_labels)

    print(f"Sentiment Accuracy:        {sentiment_metrics['accuracy']:.2%}")
    print(f"Sentiment Macro F1:        {sentiment_metrics['macro_f1']:.4f}")
    print(
        f"Sentiment Latency:         {sentiment_duration:.2f}s ({sentiment_throughput:.1f} items/sec)"
    )
    print()

    # 2. Evaluate Topic Classification
    print("Running Topic Classification (MiniLM Prototype Centroids)...")
    start_t = time.perf_counter()
    topic_results = classify_topics_batch(texts)
    topic_duration = time.perf_counter() - start_t
    pred_topics = [r.topic for r in topic_results]
    topic_throughput = len(texts) / topic_duration if topic_duration > 0 else 0.0

    topic_metrics = compute_metrics(true_topics, pred_topics, TOPIC_SET)
    topic_cm = compute_confusion_matrix(true_topics, pred_topics, TOPIC_SET)

    print(f"Topic Accuracy:            {topic_metrics['accuracy']:.2%}")
    print(f"Topic Macro F1:            {topic_metrics['macro_f1']:.4f}")
    print(f"Topic Latency:             {topic_duration:.2f}s ({topic_throughput:.1f} items/sec)")
    print("=" * 60)

    results_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sample_size": len(samples),
        "sentiment": {
            "metrics": sentiment_metrics,
            "throughput_items_per_sec": round(sentiment_throughput, 1),
            "duration_seconds": round(sentiment_duration, 3),
            "confusion_matrix": sentiment_cm,
        },
        "topics": {
            "metrics": topic_metrics,
            "throughput_items_per_sec": round(topic_throughput, 1),
            "duration_seconds": round(topic_duration, 3),
            "confusion_matrix": topic_cm,
        },
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print(f"Full evaluation metrics saved to {RESULTS_PATH}")
    return results_data


if __name__ == "__main__":
    run_evaluation()
