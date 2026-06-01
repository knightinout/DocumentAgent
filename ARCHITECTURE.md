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
| Vector Knowledge Base | AWS Bedrock Knowledge Base + OpenSearch Serverless |
| Agent Framework | Strands Agents — `agent.py` |
| Foundation Model | Amazon Bedrock (Claude 3.5 Sonnet) |
| Language | Python 3.10+ |

---

## AWS Setup — What to Create

Use **us-east-1** or **us-west-2** (Bedrock is not available in all regions).

| # | Resource | Console Link | Notes |
|---|---|---|---|
| 1 | Landing AI API key | [app.landing.ai](https://app.landing.ai/) | Store in Secrets Manager, not .env |
| 2 | S3 bucket | [S3 Console](https://console.aws.amazon.com/s3/) | Block all public access; versioning ON |
| 3 | Secrets Manager secret | [Secrets Manager Console](https://console.aws.amazon.com/secretsmanager/) | Name: `documentagent/landing-ai-key` |
| 4 | IAM role for Lambda | [IAM Console](https://console.aws.amazon.com/iam/) | Attach `infra/lambda_role_policy.json` |
| 5 | Lambda function | [Lambda Console](https://console.aws.amazon.com/lambda/) | Runtime Python 3.12, 1 GB RAM, 5 min timeout |
| 6 | S3 event notification | S3 → bucket → Properties → Event notifications | Trigger: `ObjectCreated`, prefix `*/input/` → Lambda |
| 7 | Bedrock model access | [Bedrock Model Access](https://console.aws.amazon.com/bedrock/home#/modelaccess) | Enable Titan Embed v2 + Claude 3.5 Sonnet |
| 8 | Bedrock Knowledge Base | [Bedrock Knowledge Bases](https://console.aws.amazon.com/bedrock/home#/knowledge-bases) | Data source: S3 `*/output/*`; attach `infra/bedrock_kb_role_policy.json` |
| 9 | IAM role for Bedrock KB | [IAM Console](https://console.aws.amazon.com/iam/) | Attach `infra/bedrock_kb_role_policy.json` |

After creating the KB, copy **Knowledge Base ID** and **Data Source ID** into `.env` as `BEDROCK_KB_ID` and `BEDROCK_DS_ID`.

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
