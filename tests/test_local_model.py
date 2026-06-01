"""Unit tests for LocalModelClient.

All HTTP calls are mocked — no LM Studio instance required.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from local_model import LocalModelClient, LocalModelResponse, LocalModelMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completion(text: str) -> MagicMock:
    """Build a minimal fake openai ChatCompletion response."""
    choice = MagicMock()
    choice.message.content = text
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def _make_client_mock(response_text: str = "## Extracted\nSome content") -> MagicMock:
    """Return a mock OpenAI client whose chat.completions.create returns response_text."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_completion(response_text)
    return mock_client


# ---------------------------------------------------------------------------
# Test: basic markdown return from LM Studio
# ---------------------------------------------------------------------------

class TestReturnsMarkdown:
    def test_returns_markdown_from_lm_studio(self, tmp_path):
        """parse() on an image file returns a LocalModelResponse with .markdown."""
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # minimal PNG header

        mock_client = _make_client_mock("# Invoice\n**Total**: 100")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient(base_url="http://localhost:1234/v1", model="test-model")
            result = client.parse(img)

        assert isinstance(result, LocalModelResponse)
        assert "Invoice" in result.markdown
        assert "Total" in result.markdown

    def test_returns_local_model_response_type(self, tmp_path):
        img = tmp_path / "doc.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)  # minimal JPEG header

        mock_client = _make_client_mock("some markdown")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient()
            result = client.parse(img)

        assert isinstance(result, LocalModelResponse)
        assert isinstance(result.metadata, LocalModelMetadata)


# ---------------------------------------------------------------------------
# Test: PDF converted page-by-page
# ---------------------------------------------------------------------------

class TestPdfPageByPage:
    def test_pdf_converted_page_by_page(self, tmp_path):
        """Each PDF page generates exactly one API call."""
        pdf_path = tmp_path / "doc.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_client = _make_client_mock("page content")

        # Mock pymupdf (fitz) to return 3 pages
        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_pixmap.tobytes.return_value = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
        mock_page.get_pixmap.return_value = mock_pixmap

        mock_fitz_doc = MagicMock()
        mock_fitz_doc.__len__ = lambda self: 3
        mock_fitz_doc.load_page.return_value = mock_page

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_fitz_doc
        mock_fitz.Matrix.return_value = MagicMock()

        with patch("local_model.OpenAI", return_value=mock_client), \
             patch.dict("sys.modules", {"fitz": mock_fitz}):
            client = LocalModelClient()
            result = client.parse(pdf_path)

        assert mock_client.chat.completions.create.call_count == 3
        assert result.metadata.page_count == 3

    def test_pdf_page_count_matches_pages(self, tmp_path):
        pdf_path = tmp_path / "single.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")

        mock_client = _make_client_mock("content")

        mock_page = MagicMock()
        mock_pixmap = MagicMock()
        mock_pixmap.tobytes.return_value = b"\x89PNG\r\n\x1a\n"
        mock_page.get_pixmap.return_value = mock_pixmap

        mock_fitz_doc = MagicMock()
        mock_fitz_doc.__len__ = lambda self: 1
        mock_fitz_doc.load_page.return_value = mock_page

        mock_fitz = MagicMock()
        mock_fitz.open.return_value = mock_fitz_doc
        mock_fitz.Matrix.return_value = MagicMock()

        with patch("local_model.OpenAI", return_value=mock_client), \
             patch.dict("sys.modules", {"fitz": mock_fitz}):
            client = LocalModelClient()
            result = client.parse(pdf_path)

        assert result.metadata.page_count == 1


# ---------------------------------------------------------------------------
# Test: ConnectionError → RuntimeError
# ---------------------------------------------------------------------------

class TestRaisesOnConnectionError:
    def test_raises_runtime_error_on_connection_error(self, tmp_path):
        """ConnectionError from openai is surfaced as RuntimeError with helpful message."""
        img = tmp_path / "doc.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        mock_client = MagicMock()
        # Create a class named "APIConnectionError" dynamically to simulate openai's error
        FakeAPIConnectionError = type("APIConnectionError", (Exception,), {})
        mock_client.chat.completions.create.side_effect = FakeAPIConnectionError("Connection refused")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient(base_url="http://localhost:1234/v1")
            with pytest.raises(RuntimeError) as exc_info:
                client.parse(img)

        assert "LM Studio is not reachable" in str(exc_info.value)
        assert "localhost:1234" in str(exc_info.value)
        assert "Start Server" in str(exc_info.value)

    def test_error_message_includes_base_url(self, tmp_path):
        img = tmp_path / "doc.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        mock_client = MagicMock()
        FakeConnectTimeout = type("ConnectTimeout", (Exception,), {})
        mock_client.chat.completions.create.side_effect = FakeConnectTimeout("timeout")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient(base_url="http://192.168.1.10:1234/v1")
            with pytest.raises(RuntimeError) as exc_info:
                client.parse(img)

        assert "192.168.1.10:1234" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Test: metadata shape
# ---------------------------------------------------------------------------

class TestMetadataShape:
    def test_metadata_has_page_count_and_duration(self, tmp_path):
        img = tmp_path / "doc.jpeg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 50)

        mock_client = _make_client_mock("content")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient()
            result = client.parse(img)

        assert hasattr(result.metadata, "page_count")
        assert hasattr(result.metadata, "duration_ms")
        assert result.metadata.page_count == 1
        assert isinstance(result.metadata.duration_ms, int)
        assert result.metadata.duration_ms >= 0

    def test_duration_ms_is_non_negative(self, tmp_path):
        img = tmp_path / "doc.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

        mock_client = _make_client_mock("ok")

        with patch("local_model.OpenAI", return_value=mock_client):
            client = LocalModelClient()
            result = client.parse(img)

        assert result.metadata.duration_ms >= 0


# ---------------------------------------------------------------------------
# Test: env var base URL
# ---------------------------------------------------------------------------

class TestEnvVarBaseUrl:
    def test_uses_env_var_base_url(self, tmp_path, monkeypatch):
        """LocalModelClient picks up LM_STUDIO_BASE_URL from environment."""
        monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://custom-host:5678/v1")
        monkeypatch.setenv("LOCAL_MODEL_NAME", "custom-model")

        captured_base_url = {}

        def fake_openai(**kwargs):
            captured_base_url["base_url"] = kwargs.get("base_url")
            return _make_client_mock("content from env")

        with patch("local_model.OpenAI", side_effect=fake_openai):
            client = LocalModelClient()

        assert client._base_url == "http://custom-host:5678/v1"
        assert captured_base_url["base_url"] == "http://custom-host:5678/v1"

    def test_constructor_arg_overrides_env_var(self, monkeypatch):
        """Explicit constructor argument takes precedence over env var."""
        monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://env-host:1234/v1")

        with patch("local_model.OpenAI", return_value=MagicMock()):
            client = LocalModelClient(base_url="http://explicit-host:9999/v1")

        assert client._base_url == "http://explicit-host:9999/v1"

    def test_default_base_url_when_no_env(self, monkeypatch):
        """Falls back to http://localhost:1234/v1 when env var is absent."""
        monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)

        with patch("local_model.OpenAI", return_value=MagicMock()):
            client = LocalModelClient()

        assert client._base_url == "http://localhost:1234/v1"


# ---------------------------------------------------------------------------
# Test: unsupported file type
# ---------------------------------------------------------------------------

class TestUnsupportedFileType:
    def test_raises_value_error_for_unsupported_extension(self, tmp_path):
        doc = tmp_path / "doc.tiff"
        doc.write_bytes(b"\x00" * 10)

        with patch("local_model.OpenAI", return_value=MagicMock()):
            client = LocalModelClient()
            with pytest.raises(ValueError, match="Unsupported file type"):
                client.parse(doc)
