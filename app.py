import json
import logging
import logging.handlers
import os
import tempfile
import uuid
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from landingai_ade import LandingAIADE

import storage
from local_model import LocalModelClient

_log_handler = logging.handlers.RotatingFileHandler(
    "documentagent.log", maxBytes=10 * 1024 * 1024, backupCount=3
)
_log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logging.basicConfig(level=logging.DEBUG, handlers=[_log_handler])

load_dotenv()

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.set_page_config(page_title="DocumentAgent", page_icon="📄", layout="wide")

# ── Global CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hero */
    .da-hero { padding: 1.5rem 0 0.25rem 0; }
    .da-hero h1 { font-size: 2.2rem; font-weight: 800; margin: 0 0 0.25rem 0; letter-spacing: -0.5px; }
    .da-hero p  { font-size: 1.05rem; color: #6c757d; margin: 0 0 0.75rem 0; }

    /* Badges */
    .da-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .da-badge {
        display: inline-flex; align-items: center; gap: 5px;
        font-size: 0.78rem; font-weight: 600;
        padding: 3px 11px; border-radius: 999px; letter-spacing: 0.02em;
    }
    .da-badge-privacy { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .da-badge-local   { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }

    /* Mode banner */
    .da-banner {
        padding: 10px 16px; border-radius: 8px;
        margin-bottom: 1.25rem; font-size: 0.92rem; font-weight: 500;
        border-left: 4px solid;
    }
    .da-banner-local   { background: #e3f2fd; color: #1565c0; border-color: #1565c0; }
    .da-banner-preview { background: #fff8e1; color: #e65100; border-color: #f57c00; }
    .da-banner-cloud   { background: #e8f5e9; color: #1b5e20; border-color: #388e3c; }

    /* How it works card */
    .da-howto {
        background: #f8f9fa; border: 1px solid #dee2e6;
        border-radius: 10px; padding: 1.1rem 1.4rem; margin-bottom: 1.5rem;
    }
    .da-howto h3 { font-size: 0.95rem; font-weight: 700; margin: 0 0 0.7rem 0; color: #343a40; }
    .da-steps { display: flex; gap: 2rem; flex-wrap: wrap; }
    .da-step  { display: flex; align-items: flex-start; gap: 10px; }
    .da-step-num {
        width: 26px; height: 26px; border-radius: 50%;
        background: #0d6efd; color: white;
        font-size: 0.78rem; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0; margin-top: 1px;
    }
    .da-step-text { font-size: 0.87rem; color: #495057; line-height: 1.45; }
    .da-step-sub  { color: #adb5bd; }

    /* Section labels */
    .da-label {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.08em; color: #6c757d; margin-bottom: 0.5rem;
    }

    /* Metadata chips */
    .da-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0.75rem; }
    .da-chip {
        background: #f1f3f5; color: #495057;
        font-size: 0.78rem; font-weight: 600;
        padding: 3px 10px; border-radius: 999px; border: 1px solid #dee2e6;
    }

    /* Result scrollable area */
    .da-result-scroll {
        border: 1px solid #dee2e6; border-radius: 10px;
        background: #ffffff; max-height: 520px; overflow-y: auto;
        padding: 1rem 1.2rem;
    }

    /* Doc preview panel */
    .da-doc-panel {
        border: 1px solid #dee2e6; border-radius: 10px;
        background: #f8f9fa; min-height: 300px;
        display: flex; align-items: center; justify-content: center;
        padding: 0.75rem; overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_sample_files() -> list[str]:
    samples_dir = Path("samples")
    if not samples_dir.is_dir():
        return []
    return [
        f.name
        for f in sorted(samples_dir.iterdir())
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def render_pdf_first_page(path: str) -> bytes | None:
    """Return PNG bytes for the first page of a PDF (for preview only)."""
    try:
        import fitz
        doc = fitz.open(path)
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = pix.tobytes("png")
        doc.close()
        return img
    except Exception:
        return None


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("**DocumentAgent**")
st.sidebar.caption("Local-first document intelligence")
st.sidebar.divider()

st.sidebar.markdown("**Extraction Backend**")
extraction_backend = st.sidebar.radio(
    "Extraction Backend",
    options=["Cloud (Landing AI)", "Local (LM Studio)"],
    label_visibility="collapsed",
    help=(
        "Cloud: sends documents to Landing AI servers for high-accuracy extraction.\n"
        "Local: runs Gemma 3 4B on your machine via LM Studio — no data leaves your device."
    ),
)
use_local = extraction_backend == "Local (LM Studio)"

st.sidebar.divider()
st.sidebar.markdown("**Landing AI API Key**")
env_key = os.getenv("VISION_AGENT_API_KEY", "")
api_key = st.sidebar.text_input(
    "Landing AI API Key",
    value=env_key,
    type="password",
    disabled=use_local,
    label_visibility="collapsed",
    placeholder="Paste key here…",
    help="Set VISION_AGENT_API_KEY in your .env file, or paste it here. Not required for Local backend.",
)

if "last_api_key" not in st.session_state:
    st.session_state.last_api_key = api_key
    st.session_state.is_preview_mode = not bool(api_key.strip()) and not use_local
elif st.session_state.last_api_key != api_key:
    st.session_state.is_preview_mode = not bool(api_key.strip()) and not use_local
    st.session_state.last_api_key = api_key

if use_local:
    st.session_state.is_preview_mode = False

is_preview_mode = st.session_state.is_preview_mode

st.sidebar.divider()
st.sidebar.markdown("**Mode**")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Demo Mode", use_container_width=True, disabled=use_local):
        st.session_state.is_preview_mode = True
with col2:
    if st.button("Full Mode", use_container_width=True, disabled=use_local):
        st.session_state.is_preview_mode = False

if not use_local:
    st.sidebar.divider()
    st.sidebar.markdown("**Model**")
    model = st.sidebar.selectbox(
        "Model",
        options=["dpt-2-latest", "dpt-2-mini"],
        label_visibility="collapsed",
        format_func=lambda m: (
            "dpt-2-latest — high accuracy (3 cr/page)"
            if m == "dpt-2-latest"
            else "dpt-2-mini — faster (1.5 cr/page)"
        ),
    )
else:
    model = None

st.sidebar.divider()
st.sidebar.markdown("**Storage**")
s3_env_enabled = storage.s3_enabled()
s3_consent = st.sidebar.toggle(
    "Save to S3",
    value=s3_env_enabled,
    disabled=use_local,
    help=(
        "Save uploaded documents and extraction outputs to your S3 bucket. "
        "Requires S3_BUCKET_NAME and AWS_REGION in .env. Not available for local backend."
    ),
)

if use_local:
    st.sidebar.caption("LM Studio must be running on port 1234.")
else:
    st.sidebar.caption("Documents are sent to Landing AI servers.")

# ── Background tint based on mode ────────────────────────────────────────────
if use_local:
    bg_color = "rgba(13, 110, 253, 0.04)"
elif is_preview_mode:
    bg_color = "rgba(255, 193, 7, 0.05)"
else:
    bg_color = "rgba(25, 135, 84, 0.04)"

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{ background-color: {bg_color} !important; }}
    [data-testid="stHeader"] {{ background-color: transparent !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="da-hero">
        <h1>📄 DocumentAgent</h1>
        <p>Extract structured text from any document — privately, on your device.</p>
        <div class="da-badges">
            <span class="da-badge da-badge-privacy">🔒 Privacy First</span>
            <span class="da-badge da-badge-local">⚡ Runs Locally</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Mode banner ───────────────────────────────────────────────────────────────
if use_local:
    banner_cls = "da-banner-local"
    banner_msg = (
        "🖥️ <strong>Local Model Active</strong> — "
        "your documents never leave this machine. "
        "Running Gemma 3 4B via LM Studio on port 1234."
    )
elif is_preview_mode:
    banner_cls = "da-banner-preview"
    banner_msg = (
        "🟡 <strong>Demo Mode</strong> — "
        "showing a sample extraction. "
        "Add a Landing AI key in the sidebar to extract real documents."
    )
else:
    banner_cls = "da-banner-cloud"
    banner_msg = (
        "☁️ <strong>Cloud Mode Active</strong> — "
        "documents are sent to Landing AI for extraction."
    )

st.markdown(
    f'<div class="da-banner {banner_cls}">{banner_msg}</div>',
    unsafe_allow_html=True,
)

# ── How it works ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="da-howto">
        <h3>How it works</h3>
        <div class="da-steps">
            <div class="da-step">
                <div class="da-step-num">1</div>
                <div class="da-step-text">
                    Upload a document<br>
                    <span class="da-step-sub">PDF, PNG, or JPG</span>
                </div>
            </div>
            <div class="da-step">
                <div class="da-step-num">2</div>
                <div class="da-step-text">
                    Click Extract<br>
                    <span class="da-step-sub">Runs on your machine — no cloud needed</span>
                </div>
            </div>
            <div class="da-step">
                <div class="da-step-num">3</div>
                <div class="da-step-text">
                    Copy or download<br>
                    <span class="da-step-sub">Clean structured Markdown output</span>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Powered by "
    + ("LM Studio · Gemma 3 4B (local, no external API calls)" if use_local else "Landing AI ADE")
)

# ── Document source ───────────────────────────────────────────────────────────
sample_files = get_sample_files()

if sample_files:
    input_mode = st.radio(
        "Document source",
        options=["Upload", "Use sample"],
        horizontal=True,
    )
else:
    input_mode = "Upload"

uploaded_file = None
sample_path: Path | None = None

if input_mode == "Upload":
    uploaded_file = st.file_uploader(
        "Drop your document here",
        type=["pdf", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )
else:
    chosen_sample = st.selectbox("Select a sample document", options=sample_files)
    if chosen_sample:
        sample_path = Path("samples") / chosen_sample

# ── Extract button ────────────────────────────────────────────────────────────
if st.button("Extract →", type="primary"):

    # Preview / Demo mode (cloud only)
    if is_preview_mode and not use_local:
        with st.spinner("Extracting document (simulated)…"):
            import time
            time.sleep(1.5)

        sample_markdown = """# Invoice #INV-2023-001
**Date**: October 24, 2023
**Company**: Acme Corp Ltd.
**Address**: 123 Industrial Estate, Mumbai, MH 400001

## Items

| Description | Quantity | Unit Price (₹) | Total (₹) |
|---|---|---|---|
| Industrial Steel Pipes (Grade A) | 50 | 500.00 | 25,000.00 |
| Heavy Duty Valves | 10 | 1,500.00 | 15,000.00 |
| Installation Services | 1 | 10,000.00 | 10,000.00 |

---
**Subtotal**: ₹50,000.00
**Tax (18% GST)**: ₹9,000.00
**Grand Total**: ₹59,000.00

*Note: This is a static sample for demo mode.*
"""
        st.success("Done (Demo) — 1 page, 0 credits used, 1500ms")
        st.markdown('<div class="da-label">Extracted Text</div>', unsafe_allow_html=True)
        st.download_button(
            label="Download .md",
            data=sample_markdown,
            file_name="extracted_sample.md",
            mime="text/markdown",
        )
        st.markdown(sample_markdown)
        st.stop()

    # Cloud path: require API key
    if not use_local and not api_key.strip():
        st.error("Please enter your Landing AI API Key in the sidebar to run a full extraction.")
        st.stop()

    # Load document bytes
    doc_bytes: bytes | None = None
    suffix = ".pdf"
    doc_filename = "document"

    if input_mode == "Upload":
        if uploaded_file is None:
            st.error("Please upload a document first.")
            st.stop()
        doc_bytes = uploaded_file.read()
        suffix = Path(uploaded_file.name).suffix.lower()
        doc_filename = uploaded_file.name
    else:
        if sample_path is None or not sample_path.exists():
            st.error("Selected sample file not found.")
            st.stop()
        doc_bytes = sample_path.read_bytes()
        suffix = sample_path.suffix.lower()
        doc_filename = sample_path.name

    tmp_path: str | None = None
    pdf_preview: bytes | None = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="tmp_upload"
        ) as tmp:
            tmp.write(doc_bytes)
            tmp_path = tmp.name

        if use_local:
            client_local = LocalModelClient()
            with st.spinner("Extracting via local model — this may take a moment…"):
                response = client_local.parse(document=Path(tmp_path))

            logging.info(
                "Local parse complete | pages=%s duration_ms=%s",
                response.metadata.page_count,
                response.metadata.duration_ms,
            )
            meta = response.metadata
        else:
            client_cloud = LandingAIADE(apikey=api_key)
            with st.spinner("Extracting document…"):
                response = client_cloud.parse(document=Path(tmp_path), model=model)

            logging.info(
                "Parse complete | file=%s model=%s pages=%s credits=%s duration_ms=%s chunks=%d",
                response.metadata.filename,
                model,
                response.metadata.page_count,
                response.metadata.credit_usage,
                response.metadata.duration_ms,
                len(response.chunks),
            )
            logging.debug(
                "Chunks: %s",
                json.dumps(
                    [{"id": c.id, "type": c.type, "markdown": c.markdown} for c in response.chunks],
                    indent=2,
                ),
            )
            if response.metadata.failed_pages:
                logging.warning("Failed pages: %s", response.metadata.failed_pages)

            meta = response.metadata

        # Render PDF first page for preview while tmp_path still exists
        if suffix == ".pdf":
            pdf_preview = render_pdf_first_page(tmp_path)

    except Exception as e:
        st.error(str(e))
        st.stop()
    finally:
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink()

    # Optional S3 storage (cloud path only)
    if s3_consent and not use_local:
        try:
            s3 = storage.build_backend(st.session_state.session_id)
            s3.upload_document(doc_bytes, doc_filename)
            s3.upload_output(response.markdown, "extracted.md")
            st.sidebar.success(f"Saved to S3 (session: {st.session_state.session_id[:8]}…)")
        except RuntimeError as exc:
            st.sidebar.warning(f"S3 storage skipped: {exc}")
            logging.warning("S3 upload failed: %s", exc)

    # ── Result display ────────────────────────────────────────────────────────
    if use_local:
        chips_html = (
            f'<span class="da-chip">📄 {meta.page_count} page(s)</span>'
            f'<span class="da-chip">⏱ {meta.duration_ms} ms</span>'
            f'<span class="da-chip">🔒 Local — no data sent</span>'
        )
        st.success(f"Done — {meta.page_count} page(s), {meta.duration_ms} ms (local model, 0 credits)")
    else:
        chips_html = (
            f'<span class="da-chip">📄 {meta.page_count} page(s)</span>'
            f'<span class="da-chip">💳 {meta.credit_usage} credits</span>'
            f'<span class="da-chip">⏱ {meta.duration_ms} ms</span>'
        )
        st.success(
            f"Done — {meta.page_count} page(s), {meta.credit_usage} credits, {meta.duration_ms} ms"
        )

    col_doc, col_result = st.columns([1, 1], gap="large")

    with col_doc:
        st.markdown('<div class="da-label">Document</div>', unsafe_allow_html=True)
        if suffix in {".jpg", ".jpeg", ".png"}:
            st.image(doc_bytes, caption=doc_filename, use_container_width=True)
        elif suffix == ".pdf" and pdf_preview:
            st.image(pdf_preview, caption=f"{doc_filename} — page 1", use_container_width=True)
        else:
            st.info("Preview not available for this file type.")

    with col_result:
        st.markdown('<div class="da-label">Extracted Text</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="da-chips">{chips_html}</div>', unsafe_allow_html=True)
        st.download_button(
            label="Download .md",
            data=response.markdown,
            file_name="extracted.md",
            mime="text/markdown",
        )
        st.markdown(response.markdown)
