import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from landingai_ade import LandingAIADE

logging.basicConfig(
    filename="documentagent.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

load_dotenv()

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

st.set_page_config(page_title="DocumentAgent", layout="wide")


def get_sample_files() -> list[str]:
    samples_dir = Path("samples")
    if not samples_dir.is_dir():
        return []
    return [
        f.name
        for f in sorted(samples_dir.iterdir())
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


# --- Sidebar ---
st.sidebar.header("Configuration")

env_key = os.getenv("VISION_AGENT_API_KEY", "")
api_key = st.sidebar.text_input(
    "Landing AI API Key",
    value=env_key,
    type="password",
    help="Set VISION_AGENT_API_KEY in your .env file, or paste it here.",
)

is_preview_mode = not bool(api_key.strip())

model = st.sidebar.selectbox(
    "Model",
    options=["dpt-2-latest", "dpt-2-mini"],
    format_func=lambda m: (
        "dpt-2-latest (higher accuracy, 3 credits/page)"
        if m == "dpt-2-latest"
        else "dpt-2-mini (faster, 1.5 credits/page)"
    ),
)

st.sidebar.info(
    "Documents are sent to Landing AI servers. "
    "For sensitive documents, use local mode (Phase 2)."
)

# --- Main area ---
if is_preview_mode:
    st.title("DocumentAgent (Preview Mode)")
    st.markdown(
        """
        <div style="background-color:#fff3cd; color:#856404; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #ffeeba; font-size:16px;">
            <strong> PREVIEW MODE ACTIVE</strong><br>
            No Landing AI API Key was provided. You can explore the UI, but extraction will use a static sample.<br>
            Get a key at <a href="https://landing.ai" target="_blank" style="color:#856404; font-weight:bold; text-decoration:underline;">landing.ai</a> and enter it in the sidebar to enable full extraction.
        </div>
        """,
        unsafe_allow_html=True
    )
    with st.expander("Watch Demo Video"):
        st.video("https://youtu.be/JJOMELVWtwg")  # Placeholder video
else:
    st.title("DocumentAgent (Full Mode)")
    st.markdown(
        """
        <div style="background-color:#d1e7dd; color:#0f5132; padding:15px; border-radius:8px; margin-bottom:20px; border:1px solid #badbcc; font-size:16px;">
            <strong>FULL MODE ACTIVE</strong><br>
            API Key detected. Documents will be sent to Landing AI for actual extraction.
        </div>
        """,
        unsafe_allow_html=True
    )

st.caption("Extract markdown text from documents using Landing AI AIDE.")

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
        "Upload a document",
        type=["pdf", "png", "jpg", "jpeg"],
    )
else:
    chosen_sample = st.selectbox("Select a sample document", options=sample_files)
    if chosen_sample:
        sample_path = Path("samples") / chosen_sample

# --- Extract button ---
if st.button("Extract", type="primary"):
    if is_preview_mode:
        with st.spinner("Extracting document (simulated)…"):
            import time
            time.sleep(1.5)
            
        st.success("Done (Simulated) — 1 page(s), 0 credits used, 1500ms")
        
        sample_markdown = """# Invoice #INV-2023-001
**Date**: October 24, 2023
**Company**: Acme Corp Ltd.
**Address**: 123 Industrial Estate, Mumbai, MH, 400001

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

*Note: This is a static sample for preview mode.*
"""
        
        st.download_button(
            label="Download extracted text (.md)",
            data=sample_markdown,
            file_name="extracted_sample.md",
            mime="text/markdown",
        )
        st.markdown("---")
        st.markdown(sample_markdown)
        st.stop()

    doc_bytes: bytes | None = None
    suffix = ".pdf"

    if input_mode == "Upload":
        if uploaded_file is None:
            st.error("Please upload a document first.")
            st.stop()
        doc_bytes = uploaded_file.read()
        suffix = Path(uploaded_file.name).suffix.lower()
    else:
        if sample_path is None or not sample_path.exists():
            st.error("Selected sample file not found.")
            st.stop()
        doc_bytes = sample_path.read_bytes()
        suffix = sample_path.suffix.lower()

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix="tmp_upload"
        ) as tmp:
            tmp.write(doc_bytes)
            tmp_path = tmp.name

        client = LandingAIADE(apikey=api_key)

        with st.spinner("Extracting document…"):
            response = client.parse(document=Path(tmp_path), model=model)

    except Exception as e:
        st.error(str(e))
        st.stop()
    finally:
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink()

    # Log technical details for developers
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

    # User-facing output
    meta = response.metadata
    st.success(
        f"Done — {meta.page_count} page(s), {meta.credit_usage} credits used, "
        f"{meta.duration_ms}ms"
    )

    st.download_button(
        label="Download extracted text (.md)",
        data=response.markdown,
        file_name="extracted.md",
        mime="text/markdown",
    )

    st.markdown("---")
    st.markdown(response.markdown)
