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

2. **Local path (Gemma 3 4B via LM Studio)**: An on-device pipeline using Gemma 3 4B (VLM variant) served by [LM Studio](https://lmstudio.ai) for users who prefer not to send documents to external servers. No external API calls during inference.

3. **Web demo (Streamlit)**: Developers can explore the interface freely; actual agent extraction requires a Landing AI API key or local model setup.

---

## Key Features

- Extract **text, tables, and key-value pairs** from scanned or photographed Indian documents
- Supports both **handwritten and printed** input
- **Dual-mode inference**: cloud API (Landing AI AIDE) or local model (Gemma 3 4B via LM Studio)
- Interactive **Streamlit web demo** and **Jupyter notebook** for feasibility testing
- **AWS-hosted production backend**: S3, Lambda, Bedrock, Strands Agents
- **Privacy controls**: choose between cloud processing or fully local inference — no documents sent to external servers in local mode
- No document storage by default — opt-in logging only

---

## Architecture

A dual-mode pipeline routes documents through either the Landing AI AIDE cloud API or a local quantized Gemma model, then surfaces structured output via a Streamlit interface backed by an optional AWS production layer.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full diagram, technical stack, privacy model, pricing tiers, and hardware prerequisites.

---

## Roadmap

Planned work is tracked as GitHub Issues. See the [Issues tab](https://github.com/knightinout/DocumentAgent/issues) for the full backlog, organised by phase label (`phase1-web-ui-mvp`, `phase2-local-documentagent`, `phase3-production-deploy`).

### V1 — Document Extraction (current)

Upload any document (PDF, image) and get clean structured Markdown output. Runs fully locally via Gemma 3 4B on LM Studio — no data leaves the device.

### V2 — Privacy-First Form Fill from Multiple ID Documents

**Goal:** User uploads multiple identity documents; the app extracts fields from each and auto-fills a target form, producing a ready-to-submit output — without any document leaving the machine.

**Primary use case — Lease Agreement (India):**

1. User uploads **Aadhaar card** and **driving licence** (tenant + landlord)
2. Local model extracts: name, address, DOB, ID numbers from each document
3. App maps extracted fields onto a **standard lease agreement template**
4. User reviews the pre-filled form and confirms
5. With consent, the **signature extracted from the ID document** is placed on the agreement
6. Final signed PDF is generated — ready for submission at the sub-registrar office

**Why local model matters here:** ID documents contain PAN, Aadhaar, address, photo, and signature. Running inference locally ensures this data is never transmitted to any external server. Privacy is not a feature — it is the architecture.

**Planned UI additions for V2:**
- Multi-file upload panel (drag multiple documents at once)
- Field extraction review table (editable before form fill)
- Form template selector (lease, rent receipt, affidavit, etc.)
- Signature placement preview with consent checkbox
- Final PDF download

---

## Prerequisites

- Python 3.10+
- [Landing AI API key](https://landing.ai) — required for the cloud extraction path

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/knightinout/DocumentAgent.git
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

## Phase 2 — Local Model Setup (LM Studio)

The **Local (LM Studio)** backend lets you extract documents entirely on your own machine — no documents leave your device during inference.

### Requirements
- [LM Studio](https://lmstudio.ai) installed (free)
- ~2.5 GB disk space for the model
- GPU recommended (8 GB VRAM+); CPU inference works but is slow

### Setup steps

1. Download [LM Studio](https://lmstudio.ai) and install it.
2. In LM Studio, search for **`gemma-3-4b-instruct`** and download the **VLM variant** (Q4_K_M, ~2.5 GB).
   > **Important:** Use the VLM (vision-language) variant — text-only quantizations silently drop image input. Look for `gemma-3-4b-it` with vision support, not a text-only GGUF.
3. Start the local server: **Developer tab → Start Server** (port 1234). The model loads in 10–30 seconds on first start.
4. In your `.env`, set:
   ```
   LM_STUDIO_BASE_URL=http://localhost:1234/v1
   LOCAL_MODEL_NAME=gemma-3-4b-instruct   # copy exact ID from LM Studio Developer tab
   ```
5. In the Streamlit sidebar, select **Local (LM Studio)** under Extraction Backend and click **Extract**.

> If LM Studio is not running when you click Extract, you will see a clear error: *"LM Studio is not reachable — open LM Studio and click Start Server in the Developer tab."*

---

## Running the Notebook

`notebook/DocumentAgent_notebook.ipynb` demonstrates DocumentAgent's AIDE-powered extraction with Tesseract shown as a legacy OCR baseline.

```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook notebook/DocumentAgent_notebook.ipynb
```

A valid `VISION_AGENT_API_KEY` in your `.env` is required for the Landing AI cells. The Tesseract cells run fully offline.

> **Note:** Tesseract must be installed at the OS level.
> - Linux: `sudo apt install tesseract-ocr`
> - macOS: `brew install tesseract`
> - Windows: [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Phase 3 — AWS Production Setup

> Use **us-east-1** or **us-west-2** — Bedrock is not available in all regions.

### Automated setup (recommended)

All AWS resources are created by a single script — no console required:

```bash
cp .env.example .env   # add VISION_AGENT_API_KEY + AWS_ACCESS_KEY_ID/SECRET
source .venv/bin/activate
pip install -r requirements.txt
python scripts/check_bedrock.py   # confirm model access before proceeding
python scripts/setup_aws.py       # creates all 7 resources, writes IDs to .env
```

The script creates: S3 bucket, Secrets Manager secret, IAM roles, Lambda function,
S3 event trigger, OpenSearch Serverless collection + vector index, and Bedrock
Knowledge Base. It is idempotent — safe to re-run if interrupted.

### Query documents with the Strands Agent

```bash
python agent.py "What is the total amount on the invoice?"
# or interactive:
python agent.py
```

### Agent model options

| Stage | Set `BEDROCK_MODEL_ID` in `.env` | Notes |
|---|---|---|
| Testing (default) | `amazon.nova-lite-v1:0` | No Anthropic payment gate, ~$0.003/10 queries |
| Pre-demo | `anthropic.claude-haiku-4-5-20251001-v1:0` | Fast, high quality, ~$0.05/10 queries |
| Demo | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` | Best accuracy, ~$0.17/10 queries |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full pipeline diagram, cost breakdown, and IAM policy details.

---

## Running Tests

```bash
source .venv/bin/activate
pip install pytest pytest-cov
pytest tests/ -v --cov=storage --cov=handler --cov=local_model --cov-report=term-missing
```

All tests are mocked — no AWS credentials or LM Studio instance required.

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
- [LM Studio](https://lmstudio.ai)
- [Streamlit](https://streamlit.io)
