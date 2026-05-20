# DocumentAgent — Architecture & Technical Reference

---

## Architecture Diagram

```
Input (image / PDF)
        │
        ▼
┌───────────────────────────────┐
│    Streamlit Web App / API    │  ← Demo & integration layer
└──────────────┬────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
 Cloud Path         Local Path
 (Landing AI        (Gemma 3/4
  AIDE API)          quantized)
      │                 │
      └────────┬────────┘
               ▼
      Structured Output
      (JSON / table / form)
               │
      ┌────────▼────────┐
      │   AWS Backend   │  ← Production deployment
      │  S3 / Lambda /  │
      │ Bedrock / Strands│
      └─────────────────┘
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| Document Extraction API | Landing AI AIDE (LandingAI Platform) |
| OCR Baseline | Tesseract, PaddleOCR |
| Document Understanding | LayoutLM, LayoutReader |
| Local Vision Model | Gemma 3 / Gemma 4 (4B–8B, quantized GGUF) |
| Local Inference Runtime | Ollama, llama.cpp |
| Demo Interface | Streamlit, Jupyter Notebook |
| Cloud Storage | AWS S3 (boto3) |
| Serverless Compute | AWS Lambda |
| Permissions | AWS IAM |
| Foundation Model Cloud | AWS Bedrock (bedrock-agentcore) |
| Agent Framework | Strands Agents (strands-agents) |
| Language | Python 3.10+ |

---

## Privacy & Security

| Path | Where documents go | Recommendation |
|---|---|---|
| Cloud (Landing AI / AWS) | Sent to external servers | Suitable for non-sensitive business documents |
| Local (Gemma) | Never leave the device | Recommended for Aadhaar, PAN, financial records |

- The UI clearly indicates which path is active before a document is submitted.
- No document storage by default; opt-in logging only.
- Local mode is fully air-gapped — no network calls after model download.

---

## Access & Pricing Model

| Tier | Free | Paid |
|---|---|---|
| Web Demo (Dev) | UI exploration, preview video | Actual agent extraction (requires Landing AI API key) |
| Local Mode | Full extraction on own hardware | — |
| Production API | — | Per-document pricing (TBD) |

---

## Prerequisites

- Python 3.10+
- [Landing AI API key](https://landing.ai) — required for the cloud extraction path
- AWS credentials — required for production deployment (S3, Lambda, Bedrock)
- GPU-capable machine recommended for local models (8 GB VRAM minimum for 4B quantized; 16 GB for 8B)
