"""GET /api/v1/health — service readiness probe."""

import os

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Return service status and backend availability flags.

    Response:
        status:                  "ok"
        local_model_available:   True if LM_STUDIO_BASE_URL is configured
                                 (does not ping the server).
        cloud_api_configured:    True if VISION_AGENT_API_KEY is set.
    """
    local_model_available = bool(
        os.environ.get("LM_STUDIO_BASE_URL") or os.environ.get("LOCAL_MODEL_NAME")
    )
    cloud_api_configured = bool(os.environ.get("VISION_AGENT_API_KEY"))
    return {
        "status": "ok",
        "local_model_available": local_model_available,
        "cloud_api_configured": cloud_api_configured,
    }
