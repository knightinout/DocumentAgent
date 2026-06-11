"""Form-fill service — two-stage extract → structured-fields pipeline.

Stage 1: Run the extraction service on every uploaded document to get markdown.
Stage 2: Use the local vision model in JSON mode to extract structured fields
         defined by the requested form template.

Aadhaar numbers are masked in all output (XXXX XXXX XXXX).

Supported templates
-------------------
lease_agreement   — residential lease / rent agreement
rent_receipt      — monthly rent receipt
dl_renewal        — driving licence renewal application
affidavit         — general affidavit
bank_account      — bank account opening form

Source documents
----------------
aadhaar     — Aadhaar card (front + back)
pan         — PAN card
dl          — Driving Licence
voter_id    — Voter ID (EPIC)
"""

import json
import logging
import os
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Template definitions
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, dict[str, list[str]]] = {
    "lease_agreement": {
        "required": ["tenant_name", "landlord_name", "property_address", "monthly_rent"],
        "optional": ["start_date", "duration_months", "security_deposit"],
    },
    "rent_receipt": {
        "required": ["tenant_name", "landlord_name", "amount", "month"],
        "optional": ["property_address", "receipt_number", "payment_mode"],
    },
    "dl_renewal": {
        "required": ["applicant_name", "dl_number", "dob", "address"],
        "optional": ["vehicle_class", "blood_group", "expiry_date"],
    },
    "affidavit": {
        "required": ["deponent_name", "statement", "date"],
        "optional": ["deponent_address", "notary_name"],
    },
    "bank_account": {
        "required": ["applicant_name", "dob", "address", "pan_number"],
        "optional": ["occupation", "annual_income", "nominee_name"],
    },
}

_AADHAAR_RE = re.compile(r"\b(\d{4})\s?(\d{4})\s?(\d{4})\b")


def _mask_aadhaar(text: str) -> str:
    """Replace all Aadhaar numbers with XXXX XXXX XXXX."""
    return _AADHAAR_RE.sub("XXXX XXXX XXXX", text)


def _extract_json_from_text(text: str) -> dict:
    """Parse JSON from LLM response, tolerating markdown code-fence wrappers."""
    # Strip ```json ... ``` or ``` ... ``` wrappers if present
    stripped = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped.strip())
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed (%s); raw text: %.200s", exc, text)
        return {}


def _call_llm_json(prompt: str) -> dict:
    """Call the local LM Studio model with a JSON-extraction prompt.

    Returns an empty dict if the model is unreachable or returns unparseable output.
    """
    from openai import OpenAI

    base_url = os.environ.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    model = os.environ.get("LOCAL_MODEL_NAME", "gemma-3-4b-instruct")

    client = OpenAI(base_url=base_url, api_key="lm-studio", timeout=120.0)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or "{}"
        return _extract_json_from_text(raw)
    except Exception as exc:
        logger.warning("LLM JSON call failed: %s", exc)
        return {}


def _build_extraction_prompt(fields: list[str], markdown: str) -> str:
    field_list = ", ".join(f'"{f}"' for f in fields)
    return (
        f"You are a form-filling assistant for Indian government documents.\n"
        f"Extract the following fields from the provided document text.\n"
        f"Fields to extract: [{field_list}]\n\n"
        f"Rules:\n"
        f"- Return ONLY a valid JSON object with exactly these keys.\n"
        f"- Set the value to null if a field cannot be found.\n"
        f"- Do NOT include any explanation, markdown, or extra text.\n"
        f"- Dates should be in DD/MM/YYYY format.\n"
        f"- Monetary amounts should be numeric strings (e.g. '15000').\n\n"
        f"Document text:\n{markdown}\n\n"
        f"JSON:"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class FormFillResult:
    def __init__(
        self,
        fields: dict[str, Any],
        field_sources: dict[str, str],
        missing_fields: list[str],
    ) -> None:
        self.fields = fields
        self.field_sources = field_sources
        self.missing_fields = missing_fields


def fill(
    docs: list[tuple[bytes, str]],
    template_id: str,
    *,
    use_local: bool = True,
    api_key: str | None = None,
    model: str = "dpt-2-mini",
) -> FormFillResult:
    """Run the two-stage form-fill pipeline.

    Args:
        docs:        List of (file_bytes, filename) tuples.
        template_id: One of the keys in ``_TEMPLATES``.
        use_local:   Use local LM Studio backend for stage-1 extraction.
        api_key:     Required when ``use_local=False``.
        model:       ADE model variant (cloud only).

    Returns:
        :class:`FormFillResult` with extracted fields, sources, and missing fields.

    Raises:
        ValueError: Unknown template_id or no documents provided.
    """
    if template_id not in _TEMPLATES:
        raise ValueError(
            f"Unknown template '{template_id}'. "
            f"Available: {', '.join(_TEMPLATES)}"
        )
    if not docs:
        raise ValueError("At least one document is required.")

    template = _TEMPLATES[template_id]
    all_fields = template["required"] + template["optional"]

    # ── Stage 1: extract markdown from each document ──────────────────────
    from api.services.extraction import run as extract_run

    markdowns: list[tuple[str, str]] = []  # (markdown, filename)
    for doc_bytes, filename in docs:
        result = extract_run(
            doc_bytes, filename, use_local=use_local, api_key=api_key, model=model
        )
        markdowns.append((_mask_aadhaar(result["markdown"]), filename))
        logger.info("stage-1 extract | file=%s pages=%s", filename, result["page_count"])

    # ── Stage 2: extract structured fields from combined markdown ─────────
    combined_markdown = "\n\n---\n\n".join(
        f"[Document: {fname}]\n{md}" for md, fname in markdowns
    )
    prompt = _build_extraction_prompt(all_fields, combined_markdown)

    start = time.time()
    raw_fields = _call_llm_json(prompt)
    logger.info("stage-2 field extract | duration_ms=%d", int((time.time() - start) * 1000))

    # ── Post-process ──────────────────────────────────────────────────────
    fields: dict[str, Any] = {}
    field_sources: dict[str, str] = {}
    missing_fields: list[str] = []

    for field in all_fields:
        value = raw_fields.get(field)
        fields[field] = value
        if value is not None:
            # Attribute the field to whichever document's markdown contains its value
            source_file = _find_source(str(value), markdowns) or "unknown"
            field_sources[field] = source_file
        elif field in template["required"]:
            missing_fields.append(field)

    return FormFillResult(
        fields=fields,
        field_sources=field_sources,
        missing_fields=missing_fields,
    )


def _find_source(value: str, markdowns: list[tuple[str, str]]) -> str | None:
    """Return the filename of the first document whose markdown contains *value*."""
    if not value or value.lower() == "null":
        return None
    for md, fname in markdowns:
        if value.lower() in md.lower():
            return fname
    return markdowns[0][1] if markdowns else None


def list_templates() -> list[dict]:
    """Return a list of available template descriptors."""
    return [
        {
            "template_id": tid,
            "required_fields": tmpl["required"],
            "optional_fields": tmpl["optional"],
        }
        for tid, tmpl in _TEMPLATES.items()
    ]
