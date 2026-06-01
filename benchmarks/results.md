# Phase 2 Benchmark Results: Landing AI AIDE vs Gemma 3 4B (Local)

> **Status:** Pending — run `notebook/Phase2_Benchmark.ipynb` on Kaggle (private, T4 GPU)
> to populate this file. See the notebook for methodology and dataset details.

---

## Setup

| Item | Cloud Path | Local Path |
|---|---|---|
| Model | Landing AI AIDE (`dpt-2-mini`) | Gemma 3 4B IT (VLM, Q4_K_M) |
| Runtime | Landing AI API | LM Studio, port 1234 |
| Hardware | Cloud (Landing AI infra) | Kaggle T4 GPU (benchmark) / Local machine (prod) |
| Cost | ~1.5 credits/page | $0 (after one-time download) |

---

## Dataset

20 Indian document images across 4 categories (5 documents each):

| Category | Description |
|---|---|
| Invoices | GST invoices, retail bills, vendor invoices |
| Handwritten ledgers | Shop account books, daily expense registers |
| Government forms | Ration card applications, municipal forms |
| ID-style documents | Synthetic Aadhaar-format cards, PAN-format cards |

Source: `benchmarks/dataset/` — public domain scans + synthetically generated samples.
See notebook cell 2 for attribution.

---

## Results

*To be filled after running `notebook/Phase2_Benchmark.ipynb`.*

### Summary Table

| Document | AIDE Latency (ms) | Gemma Latency (ms) | AIDE Accuracy | Gemma Accuracy | Notes |
|---|---|---|---|---|---|
| invoice_001.jpg | — | — | — | — | |
| invoice_002.jpg | — | — | — | — | |
| ledger_001.jpg | — | — | — | — | |
| ... | | | | | |

### Aggregate

| Metric | Cloud (AIDE) | Local (Gemma 3 4B, T4) |
|---|---|---|
| Avg latency / page | — | — |
| Cost / page | ~$0.015 | $0.00 |
| Table extraction | — | — |
| Handwriting quality | — | — |
| Key-value extraction | — | — |

---

## Recommendation

> To be filled after benchmark run.

Preliminary guidance (from qualitative testing):

- **Use cloud (AIDE)** for accuracy-critical extraction where table structure, complex layouts, or mixed handwritten/printed text must be extracted reliably.
- **Use local (Gemma 3 4B via LM Studio)** when documents must not leave the machine — Aadhaar cards, PAN cards, sensitive financial records, payroll sheets. Accuracy on simple invoices and text-heavy forms is acceptable.

See [ARCHITECTURE.md](../ARCHITECTURE.md) for the full recommendation in context.
