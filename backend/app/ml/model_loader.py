"""
Lazy singleton model loader for CPU-optimized inference.
Configures project-local model caches (.cache/) and thread-safe singleton instances.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

logger = logging.getLogger(__name__)

def _resolve_writable_cache_dir(env_var: str, default_name: str) -> Path:
    val = os.environ.get(env_var)
    if val and val.strip() and not val.strip().startswith("/.cache"):
        candidate = Path(val).resolve()
    else:
        # Fallback to /tmp in containers or project root if writable
        candidate = Path("/tmp") / default_name

    try:
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    except (PermissionError, OSError):
        fallback = Path("/tmp") / default_name
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


HF_CACHE = _resolve_writable_cache_dir("HF_HOME", "huggingface")
SBERT_CACHE = _resolve_writable_cache_dir("SENTENCE_TRANSFORMERS_HOME", "sbert")

os.environ["HF_HOME"] = str(HF_CACHE)
os.environ["TRANSFORMERS_CACHE"] = str(HF_CACHE)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(SBERT_CACHE)

# Limit CPU threads to avoid saturating host cores
torch.set_num_threads(2)

# Model identifiers
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_sentiment_pipeline = None
_embedding_model = None


def get_sentiment_pipeline() -> Any:
    """Lazy load singleton sentiment pipeline."""
    from app.config import get_settings
    if get_settings().low_memory_mode:
        logger.info("Low memory mode enabled: CardiffNLP RoBERTa model not loaded.")
        return None

    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        logger.info("Loading sentiment model: %s on CPU...", SENTIMENT_MODEL_NAME)
        tokenizer = AutoTokenizer.from_pretrained(
            SENTIMENT_MODEL_NAME,
            cache_dir=str(HF_CACHE),
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            SENTIMENT_MODEL_NAME,
            cache_dir=str(HF_CACHE),
        )
        model.eval()
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            device=-1,  # Force CPU
            top_k=None,  # Return all 3 class scores for confidence estimation
            truncation=True,
            max_length=128,
        )
        logger.info("Sentiment model successfully loaded.")
    return _sentiment_pipeline


def get_embedding_model() -> Any:
    """Lazy load singleton SentenceTransformer model."""
    from app.config import get_settings
    if get_settings().low_memory_mode:
        logger.info("Low memory mode enabled: SentenceTransformers model not loaded.")
        return None

    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s on CPU...", EMBEDDING_MODEL_NAME)
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME,
            cache_folder=str(SBERT_CACHE),
            device="cpu",
        )
        logger.info("Embedding model successfully loaded.")
    return _embedding_model
