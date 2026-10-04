# Social Insights — AI Model Card

## 1. Overview & Architecture Summary

Social Insights uses a **Tiered Intelligence Architecture** designed for high throughput, zero financial cost, and complete auditability. Rather than routing all incoming social media items to expensive and slow Large Language Models, the system applies local CPU-optimized neural networks for per-item classification and selectively engages an LLM (NVIDIA NIM) only on high-level statistical aggregates and low-confidence edge cases.

---

## 2. Models Used in Production

### Model 1: Sentiment Analysis (Tier 1)
- **Model Identifier**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
- **Architecture**: RoBERTa-base (125M parameters)
- **Pretraining**: ~124M tweets (2018–2021) with continuous updates
- **Task**: 3-Class Sentiment Classification (`positive`, `neutral`, `negative`)
- **License**: MIT
- **Inference Hardware**: CPU-only (pinned to 2 worker threads)
- **Quantization / Max Length**: Truncated to 128 tokens; dynamic padding
- **Measured Accuracy**: **85.00%** on 100-sample hand-labeled ground-truth benchmark
- **Measured Macro F1**: **0.8496** (Precision: 0.8693, Recall: 0.8571)
- **CPU Throughput**: ~1.9 items/sec in batched mode (batch size 32)
- **Known Limitations**: Sarcasm, irony, and nuanced automotive engineering discussions with mixed praise/criticism can occasionally be classified as neutral.

### Model 2: Topic Classification (Tier 1)
- **Model Identifier**: `sentence-transformers/all-MiniLM-L6-v2`
- **Architecture**: 6-layer BERT-based cross-encoder / bi-encoder distillation (22.7M parameters)
- **Task**: Semantic Sentence Embeddings (384-dimensional dense vectors)
- **License**: Apache 2.0
- **Classification Method**: Cosine similarity against 8 precomputed prototype topic centroids + domain keyword boosts
- **Topic Taxonomy**:
  1. `product` (lineup, styling, specifications, trims)
  2. `pricing` (MSRP, dealer markup, discounts, financing, lease)
  3. `customer_service` (dealer care, sales staff, warranty claims, service wait times)
  4. `quality` (durability, reliability, recalls, mechanical failures, rattles)
  5. `competitors` (cross-shopping Honda, Ford, Tesla, Hyundai, Kia, Chevrolet)
  6. `complaints` (lemons, lawsuits, angry customers, buybacks, regret)
  7. `features` (infotainment, CarPlay, driver assistance, MPG, heated seats)
  8. `other` (corporate press releases, financial earnings, general remarks)
- **Measured Accuracy**: **75.00%** on 100-sample hand-labeled ground-truth benchmark
- **Measured Macro F1**: **0.7089** (Precision: 0.7246, Recall: 0.7379)
- **CPU Throughput**: ~7.5 items/sec in batched mode
- **Known Limitations**: Cross-cutting complaints that overlap with quality (e.g., "dealer won't fix my broken engine") require secondary topic tracking.

### Model 3: Executive Summary & Insight Synthesis (Tier 2)
- **Provider**: NVIDIA NIM API (OpenAI-compatible endpoints)
- **Model Identifier**: `meta/llama-3.1-8b-instruct`
- **License**: Meta Llama 3.1 Community License
- **Prompt Versions**: `summary_v1.txt`, `insights_v1.txt`
- **Context Budget**: Aggregates + max 12 sample snippets (~800 tokens prompt budget)
- **Security Defenses**: Mention texts enclosed in `<mention id="...">...</mention>` tags and declared untrusted to neutralize prompt injection attacks.
- **Failover / Degradation**: If NVIDIA NIM API key is omitted, rate limited, or unreachable, system automatically executes **Tier 3 Deterministic Template Fallback** without crashing.

---

## 3. Benchmark Evaluation Metrics (100 Hand-Labeled Samples)

### Sentiment Analysis Performance:
| Class | Support | True Positives | False Positives | False Negatives | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Positive** | 35 | 25 | 2 | 10 | 92.6% | 71.4% | 0.8065 |
| **Neutral** | 30 | 30 | 12 | 0 | 71.4% | 100.0% | 0.8333 |
| **Negative** | 35 | 30 | 1 | 5 | 96.8% | 85.7% | 0.9091 |
| **Macro Avg** | **100** | — | — | — | **86.93%** | **85.71%** | **0.8496** |

**Overall Sentiment Accuracy**: **85.00%**

#### Sentiment Confusion Matrix:
```
                Predicted Positive  Predicted Neutral  Predicted Negative
Actual Positive         25                  9                  1
Actual Neutral           0                 30                  0
Actual Negative          2                  3                 30
```

---

### Topic Classification Performance:
| Topic | Support | True Positives | Precision | Recall | F1-Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `pricing` | 17 | 16 | 94.1% | 94.1% | 0.9412 |
| `customer_service` | 15 | 13 | 86.7% | 86.7% | 0.8667 |
| `quality` | 16 | 13 | 86.7% | 81.3% | 0.8387 |
| `competitors` | 12 | 12 | 60.0% | 100.0% | 0.7500 |
| `complaints` | 7 | 7 | 70.0% | 100.0% | 0.8235 |
| `features` | 11 | 9 | 100.0% | 81.8% | 0.9000 |
| `product` | 14 | 3 | 60.0% | 21.4% | 0.3158 |
| `other` | 8 | 2 | 22.2% | 25.0% | 0.2353 |
| **Macro Avg** | **100** | — | **72.46%** | **73.79%** | **0.7089** |

**Overall Topic Accuracy**: **75.00%**

---

## 4. Inference Latency & Cost Profile

| Tier | Component | Average Latency per Item | Batch Size | Marginal Financial Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 0** | Rules & Hashing | < 0.05 ms | Single | $0.00 |
| **Tier 1** | Twitter-RoBERTa (Sentiment) | ~51.5 ms (CPU) | 32 | $0.00 |
| **Tier 1** | all-MiniLM-L6-v2 (Topics) | ~13.3 ms (CPU) | 32 | $0.00 |
| **Tier 2** | NVIDIA NIM (Llama-3.1 8B) | ~850 ms (Cloud) | Single Call | $0.00 (Free Tier) |
| **Tier 3** | Template Fallback | < 0.5 ms | Single Call | $0.00 |
