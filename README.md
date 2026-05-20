# DocumentAgent

**Agentic Document & Form Extraction for India's Tier 2/3 Cities**

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-TBD-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## Problem Statement

Manual, handwritten bookkeeping dominates small businesses and government offices in India's tier 2 and tier 3 cities. This creates real problems:

- **Error-prone**: Handwritten ledgers, invoices, and forms are transcribed manually, introducing mistakes at every step.
- **Slow**: Data entry by hand or retyping scanned documents is a significant time sink.
- **Inaccessible automation**: Existing OCR and AI extraction tools are either too expensive, require cloud connectivity, or are not designed for Indian document formats and handwriting styles.

DocumentAgent addresses these gaps with a practical, privacy-conscious extraction pipeline that works for both internet-connected and offline environments.

---

## Solution

DocumentAgent is a dual-mode agentic document extraction system:

1. **Cloud path (Landing AI AIDE)**: Uses [Landing AI's AIDE API](https://landing.ai) for high-accuracy structured extraction from scanned or photographed documents — invoices, ledgers, ID documents, government forms.

2. **Local path (Gemma 3/4 quantized)**: A fully on-device pipeline using quantized Gemma 3 or Gemma 4 (4B–8B) models for users who cannot or will not send documents to external servers.

3. **Web demo (Streamlit)**: Developers can explore the interface freely; actual agent extraction requires a Landing AI API key or local model setup.

---

## Key Features

- Extract **text, tables, and key-value pairs** from scanned or photographed Indian documents
- Supports both **handwritten and printed** input
- **Dual-mode inference**: cloud API (Landing AI AIDE) or local quantized model (Gemma via Ollama / llama.cpp)
- Interactive **Streamlit web demo** and **Jupyter notebook** for feasibility testing
- **AWS-hosted production backend**: S3, Lambda, Bedrock, Strands Agents
- **Privacy controls**: choose between cloud processing or fully local inference
- No document storage by default — opt-in logging only

---

## Architecture Overview

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

## Roadmap

### Phase 1 — API-Based Web Demo

- [x] Streamlit app with Landing AI AIDE API integration
- [ ] Jupyter notebook for feasibility testing and model comparison
- [x] Support developer API key input in UI
- [ ] Preview mode (free) vs full agent mode (paid / API key required)

### Phase 2 — Local Model Support

- [ ] Integrate Gemma 3/4 (4B–8B quantized) via Ollama or llama.cpp
- [ ] On-device inference pipeline for privacy-sensitive use cases
- [ ] Benchmark accuracy vs cloud API on Indian document types

### Phase 3 — Production AWS Deployment

- [ ] S3 for document storage
- [ ] Lambda for serverless document processing
- [ ] Bedrock + Strands Agents for orchestrated multi-step extraction
- [ ] IAM roles and policies for secure access

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

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/DocumentAgent.git
cd DocumentAgent
```

### 2. Set up API key

```bash
cp .env.example .env
```

Open `.env` and add your key (get one at [landing.ai](https://landing.ai)):

```
VISION_AGENT_API_KEY=your_key_here
```

### 3. Install and run

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**Windows**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload a document or pick a sample from the `samples/` folder, select a model, and click **Extract**.

---

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## License

License to be decided — Apache 2.0 or MIT. See `LICENSE` for details once finalized.

---

## References

- [Landing AI AIDE Documentation](#) *(link to be added)*
- [Strands Agents](https://github.com/strands-agents/strands-agents)
- [AWS Bedrock AgentCore](https://aws.amazon.com/bedrock/)
- [Gemma Model Family](https://ai.google.dev/gemma)
- [Ollama](https://ollama.com)
- [Streamlit](https://streamlit.io)
