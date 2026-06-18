han# DocumentAgent — Architecture & Technical Reference

---

## Architecture Diagram

### Phase 1/2 — Cloud & Local (Dev / Demo)

```
User uploads document (PDF / image)
        │
        ▼
┌───────────────────────────────┐
│    Streamlit Web App          │  app.py — UI, routing, result display
│  (Extraction Backend toggle)  │
└──────────────┬────────────────┘
               │
      ┌────────┴────────────────┐
      │                         │
      ▼                         ▼
 Cloud Path                Local Path
 (Landing AI               local_model.py
  AIDE API)                LocalModelClient
      │                         │
      │                         │  PDF → pymupdf renders each page
      │                         │        as PNG at 96 DPI
      │                         │
      │                         ▼
      │                  LM Studio HTTP server
      │                  localhost:1234/v1
      │                  (OpenAI-compatible REST API)
      │                         │
      │                         ▼
      │                  Gemma 3 4B (VLM variant)
      │                  vision model — on device
      │                  no data leaves the machine
      │                         │
      └────────┬────────────────┘
               ▼
      Structured Output
      (Markdown — text, tables, key-value pairs)
               │
               ▼
      Two-column result display
      (document preview │ extracted markdown)
      Optional: download .md or save to S3
```

#### Local path — end-to-end call flow

```
app.py: write uploaded bytes → /tmp/tmp_upload<hash>.jpg
    │
    ▼
LocalModelClient.parse(Path("/tmp/..."))
    │
    ├─ PDF?  → _parse_pdf()
    │              fitz.open() → per-page PNG at 96 DPI
    │              _call_vision() × N pages
    │
    └─ Image? → _parse_image()
                   read bytes
                   _call_vision() × 1
                       │
                       ▼
               base64-encode PNG bytes
               openai.chat.completions.create(
                   model  = "google/gemma-3-4b"
                   messages = [{ image_url, extraction_prompt }]
                   temperature = 0.1
                   max_tokens  = 2048
                   timeout     = 120s
               )
               → POST localhost:1234/v1/chat/completions
               ← response.choices[0].message.content
    │
    ▼
LocalModelResponse(markdown, metadata{page_count, duration_ms})
    │
app.py: finally block — temp file deleted
app.py: render result columns
```

### Phase 3 — Event-Driven Pipeline (Production)

```
User / Streamlit App
        │
        │ upload doc (PDF/image)
        ▼
┌───────────────────┐
│   AWS S3 Bucket   │  {uuid}/input/{filename}
│  (input prefix)   │
└────────┬──────────┘
         │ S3 ObjectCreated event
         ▼
┌───────────────────┐
│   AWS Lambda      │  documentagent-ade-processor
│  (handler.py)     │  • fetches Landing AI key from Secrets Manager
│                   │  • calls Landing AI ADE API
│                   │  • writes markdown → {uuid}/output/extracted.md
└────────┬──────────┘
         │ StartIngestionJob
         ▼
┌───────────────────┐
│ Bedrock Knowledge │  data source: S3 */output/*
│ Base + OpenSearch │  embedding: amazon.titan-embed-text-v2:0
│ Serverless        │
└────────┬──────────┘
         │ retrieve()
         ▼
┌───────────────────┐
│  Strands Agent    │  agent.py — interactive CLI
│  (Claude 3.5)     │  query_documents tool → KB retrieval
└───────────────────┘
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| Document Extraction API | Landing AI AIDE (`landingai-ade`) |
| OCR Baseline | Tesseract, PaddleOCR |
| Local Vision Model | Gemma 3 4B (VLM variant, Q4_K_M GGUF) — **confirmed working** |
| Local Inference Runtime | **LM Studio** (OpenAI-compatible REST server, port 1234) |
| Local Client | `local_model.py` — `LocalModelClient` wraps `openai` SDK |
| Demo Interface | Streamlit (`app.py`), Jupyter Notebook |
| Cloud Storage | AWS S3 (boto3) — `storage.py` |
| Serverless Compute | AWS Lambda — `lambda/handler.py` |
| Permissions | AWS IAM — `infra/` |
| Secrets | AWS Secrets Manager |
| AOSS REST signing | `requests-aws4auth` (SigV4 for OpenSearch Serverless) |
| Vector Knowledge Base | AWS Bedrock Knowledge Base + OpenSearch Serverless |
| Agent Framework | Strands Agents — `agent.py` |
| Default Agent Model | `amazon.nova-lite-v1:0` (AWS-native, no payment gate) |
| Language | Python 3.10+ |
| Tests | pytest + pytest-cov (`tests/`) |

---

## Benchmark: Cloud vs Local

See [`benchmarks/results.md`](benchmarks/results.md) for the full Phase 2 benchmark
comparing Landing AI AIDE vs Gemma 3 4B on 20 Indian documents (invoices, handwritten
ledgers, government forms, ID-style cards).

| Metric | Cloud (AIDE) | Local (Gemma 3 4B) |
|---|---|---|
| Overall field accuracy | **90.0%** | 78.9% |
| Avg latency / page | **2.5s** | 18.1s (CPU) / ~6s (GPU) |
| Cost per page | ~$0.015 | $0.00 |
| Hardest category | Ledgers 80.0% | Ledgers 60.0% |

**Decision rule:**

| Use case | Recommendation |
|---|---|
| Answer sheet grading, mark sheets, structured invoices | **Cloud (AIDE)** — 10 pp accuracy advantage |
| Aadhaar / PAN / medical / sensitive student PII | **Local (Gemma 3 4B)** — no data leaves machine |
| Handwritten answer sheets where marks accuracy is critical | **Cloud (AIDE)** — Gemma 60% field acc too low |
| Air-gapped school deployment | **Local (Gemma 3 4B)** — no external dependency |

The mobile app's **Settings → Extraction Backend** toggle implements this decision:
default is Cloud for accuracy; switch to Local when school policy prohibits upload of
student documents.

---

## Phase 3 — Strands Agent Model Selection

The Strands Agent only performs **Q&A on already-extracted markdown** — the generative
model never sees raw images. Choose based on stage:

| Stage | Model (`BEDROCK_MODEL_ID`) | Est. cost / 10 queries | Notes |
|---|---|---|---|
| Testing | `amazon.nova-lite-v1:0` ← **default** | ~$0.003 | AWS-native, no Anthropic payment gate |
| Pre-demo | `anthropic.claude-haiku-4-5-20251001-v1:0` | ~$0.05 | Fast, excellent quality |
| Demo | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | ~$0.17 | Best accuracy for nuanced Q&A |

To switch models at any time — no code changes needed, just update `.env`:
```
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
```

---

## Privacy & Security

| Path | Where documents go | Recommendation |
|---|---|---|
| Cloud (Landing AI) | Sent to Landing AI servers during extraction | Suitable for non-sensitive business documents |
| Local (Gemma 3 4B) | Processed on-device — no external API calls during inference | Use for Aadhaar, PAN, financial records |

- Landing AI API key stored in Secrets Manager for the Lambda path — never in env vars as plaintext.
- No document storage by default; opt-in S3 toggle in the Streamlit sidebar.
- Local mode: LM Studio requires a one-time model download (~2.5 GB). After that, no network calls during inference.

---

## Prerequisites

- Python 3.10+
- [Landing AI API key](https://app.landing.ai/) — required for cloud extraction
- AWS account with access to S3, Lambda, Bedrock, Secrets Manager — required for Phase 3
- [LM Studio](https://lmstudio.ai) with `gemma-3-4b-instruct` VLM variant — required for local extraction
- GPU recommended for local models (8 GB VRAM for 4B; 16 GB for 8B). CPU inference works but is slow.
