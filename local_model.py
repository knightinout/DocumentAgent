"""LocalModelClient — LM Studio wrapper for local document extraction.

LM Studio exposes an OpenAI-compatible REST server at http://localhost:1234/v1.
This module provides the same interface as the cloud path so app.py can use
both backends identically.

Setup:
    1. Install LM Studio from https://lmstudio.ai
    2. Load the gemma-3-4b-instruct VLM model
    3. Developer tab → Start Server (port 1234)
    4. Set LM_STUDIO_BASE_URL and LOCAL_MODEL_NAME in .env
"""

import base64
import io
import os
import time
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

_EXTRACT_PROMPT = (
    "Extract all text, tables, and key-value pairs from this document image. "
    "Return clean Markdown. Preserve table structure. Do not add commentary."
)


@dataclass
class LocalModelMetadata:
    page_count: int
    duration_ms: int


@dataclass
class LocalModelResponse:
    markdown: str
    metadata: LocalModelMetadata


class LocalModelClient:
    """Wraps LM Studio's OpenAI-compatible API for document extraction.

    Args:
        base_url: LM Studio server URL (default: http://localhost:1234/v1).
                  Override with LM_STUDIO_BASE_URL env var or pass directly.
        model: Exact model ID as shown in LM Studio's Developer tab.
               Override with LOCAL_MODEL_NAME env var or pass directly.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        resolved_base = (
            base_url
            or os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        )
        resolved_model = (
            model
            or os.environ.get("LOCAL_MODEL_NAME", "gemma-3-4b-instruct")
        )
        self._base_url = resolved_base
        self._model = resolved_model
        self._client = OpenAI(base_url=resolved_base, api_key="lm-studio", timeout=120.0)

    def parse(self, document: Path, model: str | None = None) -> LocalModelResponse:
        """Extract text, tables, and key-value pairs from a document.

        Supports PDF (converted page-by-page via pymupdf) and image files
        (JPEG, PNG). Returns a LocalModelResponse with .markdown and
        .metadata(.page_count, .duration_ms).

        Args:
            document: Path to the document file.
            model: Override the model for this call only.

        Raises:
            RuntimeError: If LM Studio is not reachable at the configured URL.
            ValueError: If the file extension is not supported.
        """
        active_model = model or self._model
        suffix = document.suffix.lower()

        start = time.time()
        try:
            if suffix == ".pdf":
                markdown, page_count = self._parse_pdf(document, active_model)
            elif suffix in {".jpg", ".jpeg", ".png"}:
                markdown, page_count = self._parse_image(document, active_model)
            else:
                raise ValueError(
                    f"Unsupported file type '{suffix}'. "
                    "Supported: .pdf, .jpg, .jpeg, .png"
                )
        except Exception as exc:
            # Detect connection failures and surface a human-readable error.
            exc_type = type(exc).__name__
            if exc_type in ("ConnectionError", "ConnectTimeout", "APIConnectionError"):
                raise RuntimeError(
                    f"LM Studio is not reachable at {self._base_url}. "
                    "Open LM Studio and click Start Server in the Developer tab."
                ) from exc
            raise

        duration_ms = int((time.time() - start) * 1000)
        return LocalModelResponse(
            markdown=markdown,
            metadata=LocalModelMetadata(page_count=page_count, duration_ms=duration_ms),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_pdf(self, path: Path, model: str) -> tuple[str, int]:
        """Convert each PDF page to an image and extract via vision endpoint."""
        import fitz  # pymupdf

        doc = fitz.open(str(path))
        pages: list[str] = []
        try:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Render at 96 DPI — reduced for CPU inference (lower memory + token cost).
                mat = fitz.Matrix(96 / 72, 96 / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                page_md = self._call_vision(img_bytes, "image/png", model)
                pages.append(page_md)
        finally:
            doc.close()

        combined = "\n\n---\n\n".join(pages) if len(pages) > 1 else (pages[0] if pages else "")
        return combined, len(pages)

    def _parse_image(self, path: Path, model: str) -> tuple[str, int]:
        """Extract text from a single image file."""
        suffix = path.suffix.lower().lstrip(".")
        mime = "image/jpeg" if suffix in ("jpg", "jpeg") else f"image/{suffix}"
        img_bytes = path.read_bytes()
        markdown = self._call_vision(img_bytes, mime, model)
        return markdown, 1

    def _call_vision(self, img_bytes: bytes, mime_type: str, model: str) -> str:
        """Send one image to the LM Studio vision endpoint and return markdown."""
        b64 = base64.b64encode(img_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{b64}"

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url},
                            },
                            {
                                "type": "text",
                                "text": _EXTRACT_PROMPT,
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=2048,
            )
        except Exception as exc:
            exc_type = type(exc).__name__
            if exc_type in ("ConnectionError", "ConnectTimeout", "APIConnectionError"):
                raise RuntimeError(
                    f"LM Studio is not reachable at {self._base_url}. "
                    "Open LM Studio and click Start Server in the Developer tab."
                ) from exc
            raise

        return response.choices[0].message.content or ""
