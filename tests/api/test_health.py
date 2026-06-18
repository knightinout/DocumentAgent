"""Tests for GET /api/v1/health."""

import pytest
from httpx import ASGITransport, AsyncClient

from api.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    @pytest.mark.anyio
    async def test_returns_200(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_response_has_required_keys(self, client):
        response = await client.get("/api/v1/health")
        body = response.json()
        assert "status" in body
        assert "local_model_available" in body
        assert "cloud_api_configured" in body

    @pytest.mark.anyio
    async def test_status_is_ok(self, client):
        response = await client.get("/api/v1/health")
        assert response.json()["status"] == "ok"

    @pytest.mark.anyio
    async def test_local_model_available_false_when_no_env(self, client, monkeypatch):
        monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)
        monkeypatch.delenv("LOCAL_MODEL_NAME", raising=False)
        response = await client.get("/api/v1/health")
        assert response.json()["local_model_available"] is False

    @pytest.mark.anyio
    async def test_local_model_available_true_when_env_set(self, client, monkeypatch):
        monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        response = await client.get("/api/v1/health")
        assert response.json()["local_model_available"] is True

    @pytest.mark.anyio
    async def test_cloud_api_configured_false_when_no_key(self, client, monkeypatch):
        monkeypatch.delenv("VISION_AGENT_API_KEY", raising=False)
        response = await client.get("/api/v1/health")
        assert response.json()["cloud_api_configured"] is False

    @pytest.mark.anyio
    async def test_cloud_api_configured_true_when_key_set(self, client, monkeypatch):
        monkeypatch.setenv("VISION_AGENT_API_KEY", "test-key-123")
        response = await client.get("/api/v1/health")
        assert response.json()["cloud_api_configured"] is True

    @pytest.mark.anyio
    async def test_response_has_x_request_id_header(self, client):
        response = await client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    @pytest.mark.anyio
    async def test_response_has_x_data_retained_header(self, client):
        response = await client.get("/api/v1/health")
        assert response.headers.get("x-data-retained") == "false"
