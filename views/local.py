"""Local extraction page — chat-based document extraction via Qwen2.5-VL-7B on Apple MLX."""

import logging
import tempfile
import threading
import time
import traceback
from pathlib import Path

import streamlit as st

from common import page_header, render_pdf_first_page, sidebar_base
from local_model import (
    DownloadProgress,
    LocalModelClient,
    download_model,
    is_model_ready,
    is_platform_supported,
)

_MB = 1024 * 1024
_CANCEL_GRACE_SECONDS = 6

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def _init_chat_state() -> None:
    st.session_state.setdefault("local_chat_messages", [])
    st.session_state.setdefault("local_model_messages", [])
    st.session_state.setdefault("local_chat_documents", [])
    st.session_state.setdefault("local_image_paths", [])
    st.session_state.setdefault("local_extracting", False)
    st.session_state.setdefault("local_downloading", False)
    st.session_state.setdefault("local_uploader_key", 0)


def _clear_chat() -> None:
    for doc in st.session_state.get("local_chat_documents", []):
        try:
            Path(doc["tmp_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    st.session_state.local_chat_messages = []
    st.session_state.local_model_messages = []
    st.session_state.local_chat_documents = []
    st.session_state.local_image_paths = []
    st.session_state.local_extracting = False
    st.session_state.local_uploader_key = st.session_state.get("local_uploader_key", 0) + 1


def _save_upload(uploaded_file) -> dict:
    """Save an uploaded file to a temp file, return doc metadata dict."""
    doc_bytes = uploaded_file.read()
    suffix = Path(uploaded_file.name).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="chat_doc_")
    tmp.write(doc_bytes)
    tmp.close()
    return {
        "name": uploaded_file.name,
        "file_id": uploaded_file.file_id,
        "bytes": doc_bytes,
        "suffix": suffix,
        "tmp_path": tmp.name,
    }


def _extract_document(doc: dict) -> None:
    """Run extraction for a single document and append results to chat."""
    client = LocalModelClient()
    name = doc["name"]

    st.session_state.local_chat_messages.append({
        "role": "user",
        "content": f"Extract text from **{name}**",
        "metadata": None,
    })

    try:
        with st.spinner(f"Extracting {name} via local model..."):
            response = client.parse(document=Path(doc["tmp_path"]))

        extraction_md = response.markdown
        meta = {"page_count": response.metadata.page_count, "duration_ms": response.metadata.duration_ms}

        st.session_state.local_model_messages.append({
            "role": "user",
            "content": f"I've uploaded a document '{name}'. Here is the extracted text:\n\n{extraction_md}\n\nThis is the raw extraction. I may ask you to refine it.",
        })
        st.session_state.local_model_messages.append({
            "role": "assistant",
            "content": extraction_md,
        })

        st.session_state.local_chat_messages.append({
            "role": "assistant",
            "content": extraction_md,
            "metadata": meta,
        })

        logging.info("Chat extraction complete | doc=%s pages=%s duration_ms=%s",
                      name, meta["page_count"], meta["duration_ms"])

    except Exception as e:
        logging.exception("Chat extraction failed for %s", name)
        error_msg = f"Extraction failed: {type(e).__name__}: {e}\n\n```\n{traceback.format_exc()}\n```"
        st.session_state.local_chat_messages.append({
            "role": "assistant",
            "content": error_msg,
            "metadata": None,
        })


def _handle_refinement(prompt: str) -> None:
    """Send a refinement prompt through multi-turn chat."""
    st.session_state.local_chat_messages.append({
        "role": "user",
        "content": prompt,
        "metadata": None,
    })
    st.session_state.local_model_messages.append({
        "role": "user",
        "content": prompt,
    })

    client = LocalModelClient()
    try:
        with st.spinner("Thinking..."):
            response = client.chat(
                st.session_state.local_model_messages,
            )
        st.session_state.local_model_messages.append({
            "role": "assistant",
            "content": response,
        })
        st.session_state.local_chat_messages.append({
            "role": "assistant",
            "content": response,
            "metadata": None,
        })
    except Exception as e:
        logging.exception("Chat refinement failed")
        error_msg = f"Error: {type(e).__name__}: {e}"
        st.session_state.local_chat_messages.append({
            "role": "assistant",
            "content": error_msg,
            "metadata": None,
        })


def _render_download_progress() -> bool:
    """Render model download progress. Returns True if still downloading."""
    if not st.session_state.get("local_downloading"):
        return False

    progress: DownloadProgress = st.session_state.local_download_progress
    cancel_event: threading.Event = st.session_state.local_download_cancel
    thread: threading.Thread = st.session_state.local_download_thread

    col_bar, col_cancel = st.columns([5, 1])
    with col_bar:
        if progress.total_bytes > 0:
            pct = progress.fraction
            shown_downloaded = min(progress.downloaded_bytes, progress.total_bytes)
            st.progress(
                pct,
                text=(
                    f"Downloading local model (first run only)... {pct * 100:.0f}%  "
                    f"({shown_downloaded / _MB:.0f} MB / "
                    f"{progress.total_bytes / _MB:.0f} MB)"
                ),
            )
        else:
            st.progress(0.0, text="Downloading local model (first run only)... preparing")
    with col_cancel:
        if st.button("Cancel", key="local_cancel_download"):
            cancel_event.set()
            st.session_state.local_cancel_requested_at = time.time()
            st.info("Cancelling...")

    if thread.is_alive():
        requested_at = st.session_state.get("local_cancel_requested_at")
        if requested_at and (time.time() - requested_at) > _CANCEL_GRACE_SECONDS:
            st.session_state.local_downloading = False
            st.session_state.pop("local_pending_extract", None)
            st.session_state.pop("local_cancel_requested_at", None)
            st.toast(
                "Cancel requested, but the download is taking a moment to stop "
                "in the background. It's safe to upload again.",
                icon="⚠️",
            )
            st.rerun()
        time.sleep(0.4)
        st.rerun()

    st.session_state.local_downloading = False
    st.session_state.pop("local_cancel_requested_at", None)
    if progress.cancelled:
        st.session_state.pop("local_pending_extract", None)
        st.toast("Download cancelled.", icon="🛑")
        st.rerun()
    if progress.error:
        st.session_state.local_download_error = progress.error
        st.session_state.pop("local_pending_extract", None)
        st.rerun()
    return False


def _start_download_if_needed(pending_docs: list[dict]) -> bool:
    """Start model download if not ready. Returns True if download was started."""
    if is_model_ready():
        return False

    progress = DownloadProgress()
    cancel_event = threading.Event()
    repo_id = LocalModelClient()._model
    thread = threading.Thread(
        target=download_model,
        args=(repo_id, progress, cancel_event),
        daemon=True,
    )
    thread.start()
    st.session_state.local_download_progress = progress
    st.session_state.local_download_cancel = cancel_event
    st.session_state.local_download_thread = thread
    st.session_state.local_downloading = True
    st.session_state.local_pending_extract = pending_docs
    return True


def _set_clipboard(msg_index: int) -> None:
    """Mark a message for clipboard copy — the JS snippet picks it up."""
    st.session_state["_clipboard_text"] = st.session_state.local_chat_messages[msg_index]["content"]


def render() -> None:
    _init_chat_state()
    sidebar_base()
    page_header(
        "Local Extraction",
        "Chat with your documents — upload, extract, and refine using Qwen2.5-VL-7B on Apple MLX.",
    )

    download_error = st.session_state.pop("local_download_error", None)
    if download_error:
        st.error(f"Model download failed: {download_error}")

    with st.sidebar:
        st.markdown("**Local Model**")
        if not is_platform_supported():
            st.caption("⚠️ Requires Apple Silicon macOS. Use Cloud mode on this machine.")
        elif is_model_ready():
            st.caption("✅ Model downloaded — ready to extract.")
        else:
            st.caption("First extraction downloads the model (~5 GB), once.")
        st.caption("Set LOCAL_MODEL_REPO in .env to use a different model.")

    st.markdown(
        """
        <div class="da-banner da-banner-local">
            🖥️ <strong>Local Model Active</strong> — your documents never leave this machine.
            Runs entirely on-device via Apple MLX — no setup, no external server.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Powered by Apple MLX · Qwen2.5-VL-7B (local, no external API calls)")

    # ── Clipboard copy via JS ─────────────────────────────────────────────
    clip_text = st.session_state.pop("_clipboard_text", None)
    if clip_text:
        safe = clip_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        st.html(
            f"<script>navigator.clipboard.writeText(`{safe}`).then(()=>{{}});</script>",
            unsafe_allow_javascript=True,
        )
        st.toast("Copied to clipboard!", icon="📋")

    # ── Model download progress ───────────────────────────────────────────
    still_downloading = _render_download_progress()

    if not still_downloading and not st.session_state.get("local_downloading"):
        pending = st.session_state.pop("local_pending_extract", None)
        if pending:
            st.session_state.local_extracting = True
            for doc in pending:
                _extract_document(doc)
            st.session_state.local_extracting = False
            st.rerun()

    # ── Chat history ──────────────────────────────────────────────────────
    for i, msg in enumerate(st.session_state.local_chat_messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                _, col_copy, col_dl = st.columns([8, 1, 1])
                with col_copy:
                    st.button("📋 Copy", key=f"copy_{i}", on_click=_set_clipboard, args=(i,))
                with col_dl:
                    doc_name = "extraction"
                    for doc in st.session_state.local_chat_documents:
                        doc_name = Path(doc["name"]).stem
                        break
                    st.download_button(
                        "⬇ .md",
                        data=msg["content"],
                        file_name=f"{doc_name}.md",
                        mime="text/markdown",
                        key=f"dl_{i}",
                    )

            if msg["role"] == "assistant" and msg.get("metadata"):
                meta = msg["metadata"]
                st.markdown(
                    f'<div class="da-chips">'
                    f'<span class="da-chip">📄 {meta["page_count"]} page(s)</span>'
                    f'<span class="da-chip">⏱ {meta["duration_ms"]} ms</span>'
                    f'<span class="da-chip">🔒 Local — no data sent</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(msg["content"])

    # ── File uploader (visible, above chat input) ───────────────────────
    uploader_key = f"local_chat_uploader_{st.session_state.local_uploader_key}"
    with st.expander("📎 Attach documents", expanded=False):
        uploaded_files = st.file_uploader(
            "Drop files here",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key=uploader_key,
            label_visibility="collapsed",
        )

    has_docs = len(st.session_state.local_chat_documents) > 0
    placeholder = "Ask to refine the extraction..." if has_docs else "Upload a document to begin..."
    prompt = st.chat_input(
        placeholder,
        key="local_chat_input",
        disabled=st.session_state.get("local_extracting", False),
    )

    # ── Detect new uploads and auto-extract ───────────────────────────────
    if uploaded_files and not st.session_state.get("local_downloading") and not st.session_state.get("local_extracting"):
        existing_ids = {d["file_id"] for d in st.session_state.local_chat_documents}
        new_files = [f for f in uploaded_files if f.file_id not in existing_ids]

        if new_files:
            new_docs = []
            for f in new_files:
                doc = _save_upload(f)
                st.session_state.local_chat_documents.append(doc)
                new_docs.append(doc)

            if _start_download_if_needed(new_docs):
                st.rerun()
            else:
                st.session_state.local_extracting = True
                for doc in new_docs:
                    _extract_document(doc)
                st.session_state.local_extracting = False
                st.rerun()

    # ── Handle refinement prompt ──────────────────────────────────────────
    if prompt and has_docs:
        _handle_refinement(prompt)
        st.rerun()
    elif prompt and not has_docs:
        st.warning("Please upload a document first.")

    # ── Clear chat ────────────────────────────────────────────────────────
    if st.session_state.local_chat_messages:
        if st.button("Clear chat", key="local_clear_chat", type="secondary"):
            _clear_chat()
            st.rerun()
