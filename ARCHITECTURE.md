# DocumentAgent — Architecture & Technical Reference

---

## Architecture Diagram

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

### Phase 1/2 — Demo & Local (Dev)

```
Input (image / PDF)
        │
        ▼
┌───────────────────────────────┐
│    Streamlit Web App          │  Demo & integration layer
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
      (Markdown / JSON)
```

---

## Strands Agent — Model Selection

The Strands Agent only performs **Q&A on already-extracted markdown** — the generative model never sees raw images. Choose based on stage:

| Stage | Model (`BEDROCK_MODEL_ID`) | Est. cost / 10 queries | Notes |
|---|---|---|---|
| Testing | `amazon.nova-lite-v1:0` ← **default** | ~$0.003 | AWS-native, no Anthropic payment gate |
| Testing alt | `google.gemma-3-12b-it` | ~$0.003 | Open-weights, on Bedrock |
| Pre-demo | `anthropic.claude-haiku-4-5-20251001-v1:0` | ~$0.05 | Fast, excellent quality |
| Demo | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | ~$0.17 | Best accuracy for nuanced Q&A |

**Chinese models** (DeepSeek, Qwen) are available on Bedrock and capable, but not recommended for demos involving business documents — data provenance questions arise with stakeholders even though inference runs on AWS infra.

**Full cost estimate for 4 sample files** (extraction + indexing + 10 test queries):

| Path | ADE extraction | Titan Embed v2 | Agent (10 queries) | Total |
|---|---|---|---|---|
| Nova Lite | ~$0.03 | < $0.001 | ~$0.003 | **~$0.035** |
| Claude Haiku | ~$0.03 | < $0.001 | ~$0.05 | **~$0.08** |
| Claude Sonnet | ~$0.03 | < $0.001 | ~$0.17 | **~$0.20** |

To switch models at any time — no code changes needed, just update `.env`:
```
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
```

---

## Technical Stack

| Layer | Technology |
|---|---|
| Document Extraction API | Landing AI AIDE (`landingai-ade`) |
| OCR Baseline | Tesseract, PaddleOCR |
| Local Vision Model | Gemma 3 / Gemma 4 (4B–8B, quantized GGUF) |
| Local Inference Runtime | Ollama, llama.cpp |
| Demo Interface | Streamlit, Jupyter Notebook |
| Cloud Storage | AWS S3 (boto3) — `storage.py` |
| Serverless Compute | AWS Lambda — `lambda/handler.py` |
| Permissions | AWS IAM — `infra/` |
| Secrets | AWS Secrets Manager |
| AOSS REST signing | `requests-aws4auth` (SigV4 for OpenSearch Serverless) |
| Vector Knowledge Base | AWS Bedrock Knowledge Base + OpenSearch Serverless |
| Agent Framework | Strands Agents — `agent.py` |
| Default Agent Model | `amazon.nova-lite-v1:0` (AWS-native, no payment gate) |
| Language | Python 3.10+ |
| Tests | pytest + pytest-cov (`tests/`) — 100% coverage on `storage.py` and `lambda/handler.py` |

---

## AWS Setup — Automated Script (Recommended)

All 7 resources are created in a single script — no console clicking required:

```bash
cp .env.example .env          # fill in VISION_AGENT_API_KEY + AWS credentials
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_aws.py   # creates everything, writes KB/DS IDs back to .env
```

The script is idempotent — re-running it skips resources that already exist.

**Before running**, verify your Bedrock model is reachable:
```bash
python scripts/check_bedrock.py
# APPROVED — amazon.nova-lite-v1:0 is reachable. Run: python scripts/setup_aws.py
```

### What the script creates

Use **us-east-1** or **us-west-2** (Bedrock is not available in all regions).

| # | Resource | Notes |
|---|---|---|
| 1 | S3 bucket | Versioning ON, public access blocked |
| 2 | Secrets Manager secret | `documentagent/landing-ai-key` — Landing AI key stored as JSON |
| 3 | IAM roles | Lambda execution role + Bedrock KB service role with least-privilege policies |
| 4 | Lambda function | `documentagent-ade-processor` — Python 3.12, 1 GB RAM, 5 min timeout |
| 5 | S3 event notification | ObjectCreated on bucket → Lambda (handler filters `*/input/*` keys) |
| 6 | Bedrock model check | Test-invokes `BEDROCK_MODEL_ID` to confirm access before KB creation |
| 7 | OpenSearch Serverless + Bedrock KB | AOSS collection, vector index (dim=1024, faiss/hnsw), KB, S3 data source |

After completion, `BEDROCK_KB_ID` and `BEDROCK_DS_ID` are written back to `.env` automatically.

---

## S3 Prefix Layout

```
{uuid}/
  input/   ← raw uploaded documents  (Lambda trigger listens here)
  output/  ← ADE-extracted markdown  (Bedrock KB data source reads here)
```

---

## Privacy & Security

| Path | Where documents go | Recommendation |
|---|---|---|
| Cloud (Landing AI / AWS) | Sent to external servers | Suitable for non-sensitive business documents |
| Local (Gemma) | Never leave the device | Recommended for Aadhaar, PAN, financial records |

- Landing AI API key stored in Secrets Manager — never in Lambda env vars as plaintext.
- No document storage by default; opt-in toggle in the Streamlit sidebar.
- Local mode is fully air-gapped — no network calls after model download.

---

## Prerequisites

- Python 3.10+
- [Landing AI API key](https://app.landing.ai/) — required for cloud extraction
- AWS account with access to S3, Lambda, Bedrock, Secrets Manager
- GPU-capable machine recommended for local models (8 GB VRAM for 4B; 16 GB for 8B)
