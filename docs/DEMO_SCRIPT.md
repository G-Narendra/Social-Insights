# Social Insights — Platform Demonstration Script (3-5 Minutes)

This script provides an interactive, step-by-step walkthrough to demonstrate the complete Social Insights platform to evaluators, stakeholders, or prospective users.

---

## Pre-Demo Checklist

1. **Start the Backend API:**
   ```bash
   .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Start the Frontend Web Dashboard:**
   ```bash
   cd frontend && npm run dev
   ```
3. **Open the Dashboard in your browser:**
   Navigate to `http://localhost:3000` (or `http://localhost:8000/docs` for the interactive OpenAPI Swagger UI).

---

## 5-Minute Demonstration Flow

### Scene 1: First Impression & Platform Health (30 Seconds)
- **Action**: Open `http://localhost:3000/`.
- **Narration**:
  > *"Welcome to Social Insights — an end-to-end, open-source social listening and market intelligence platform. Notice the clean, dark-mode glassmorphic dashboard. In the top navbar, our health probe confirms the backend is online and database connectivity is verified."*

---

### Scene 2: Live Multi-Source Collection & Ingestion (60 Seconds)
- **Action**:
  1. Click the glowing **"Collect Mentions"** button in the top right.
  2. Enter **`Toyota`** as the target keyword.
  3. Enter aliases: **`Camry, RAV4, GR Corolla`**.
  4. Select active connectors: **Hacker News**, **Google News (RSS)**, and **Stack Exchange**.
  5. Click **"Start Ingestion"**.
- **Narration**:
  > *"When we trigger collection, the platform launches an asynchronous background job. Notice the live progress indicator polling the backend: it fetches raw mentions across multiple public APIs without requiring expensive subscriptions, then routes them into our deterministic processing pipeline."*
- **Outcome**: The modal completes with *"Enrichment complete! Updating dashboard..."* and refreshes the view.

---

### Scene 3: Overview Tab & Pipeline Quality Audit (60 Seconds)
- **Action**: Review the **Overview Tab**.
- **Narration**:
  > *"Here is our executive dashboard. Notice the 4 top KPI cards: Total Mentions, Positive %, Neutral %, and Negative %. Below, we have an interactive timeline of mention frequency, as well as a semantic topic breakdown powered by local MiniLM embeddings.*
  >
  > *At the bottom, our Data Pipeline & Quality Audit card demonstrates real transparency: it shows exactly how many raw items were ingested, how many were kept, and the exact drop reasons (such as language filtering, word-boundary relevance checks, or URL deduplication)."*

---

### Scene 4: Deep Mentions Feed & Transparent Inspection (60 Seconds)
- **Action**:
  1. Click the **"Mentions Feed"** tab.
  2. Select **"Negative"** in the sentiment dropdown.
  3. Type a query like `"price"` or `"delay"` in the search bar.
  4. Click **"Read full text"** on any mention to expand it.
  5. Point to the source badge (e.g., `GOOGLENEWS`), sentiment confidence score (e.g., `Negative (0.88)`), and the **"Original"** external link.
- **Narration**:
  > *"The Mentions Feed allows analysts to search, filter, and inspect individual posts. Every mention is enriched with 3-class sentiment from a local CardiffNLP Twitter-RoBERTa model running on CPU, plus a semantic topic classification. If an item is borderline, a 'Low Confidence' badge is displayed. Clicking 'Original' links directly out to the source post on the web."*

---

### Scene 5: AI Insights & Executive Synthesis (45 Seconds)
- **Action**: Click the **"AI Insights"** tab.
- **Narration**:
  > *"This is our Tiered AI Intelligence layer. Rather than sending thousands of raw posts to an expensive LLM, our platform computes structured aggregates and sends a compact, budgeted context to an LLM (such as NVIDIA NIM Llama 3.1 8B). If no API key is provided, it automatically falls back to our zero-hallucination Tier 3 deterministic template.*
  >
  > *Notice the 5 structured intelligence categories below: Emerging Complaints, Requested Features, Pain Points, Positive Themes, and Market Opportunities — each backed by specific cited mention IDs for auditability."*

---

### Scene 6: Competitor Benchmarking & Anomaly Alerts (45 Seconds)
- **Action**:
  1. Click the **"Compare Brands"** tab (BON-02).
  2. Show the side-by-side cards for `Toyota`, `Honda`, and `Tesla` comparing mention volume, sentiment mix, and top customer complaints.
  3. Point to the top **Trends & Anomaly Alert Banner** (BON-01, BON-04) displaying topic velocity (+X% increase) or statistical negative sentiment spikes.
- **Narration**:
  > *"Finally, we have our bonus capabilities: Multi-Brand Competitor Benchmarking, allowing teams to compare share of voice and sentiment ratios across competitors, and our automated Anomaly Alert Engine that flags statistical spikes exceeding 2 standard deviations above historical baselines."*

---

### Conclusion (15 Seconds)
- **Narration**:
  > *"Social Insights provides enterprise-grade social listening with zero API costs, resilient local machine learning, and strict privacy controls. Thank you!"*
