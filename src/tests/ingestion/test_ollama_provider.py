"""
OllamaProvider unit tests: response parsing and zero-output failure handling.
No real network calls - requests.post is mocked (project rule: the LLM
provider must be mocked/faked in tests).
"""
from pathlib import Path
from unittest.mock import Mock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.app.ingestion.providers.ollama_provider import OllamaProvider, OllamaProviderConfig
from src.app.ingestion.providers.base import ExtractionResult


def _mock_response(response_text: str, done_reason: str = None):
    response = Mock()
    response.raise_for_status = Mock()
    response_json = {"response": response_text}
    if done_reason is not None:
        response_json["done_reason"] = done_reason
    response.json.return_value = response_json
    return response


def test_extract_parses_assertions():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response(
        "direct: The sky is blue.\ninferred: It rained recently."
    )

    result = provider.extract("some source text", {"source_path": "test.md"})

    assert isinstance(result, ExtractionResult)
    assert len(result.assertions) == 2
    assert result.assertions[0].epistemic_status == "direct"
    assert result.assertions[1].epistemic_status == "inferred"

    provider.requests.post.assert_called_once()
    call_kwargs = provider.requests.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "llama3"
    assert call_kwargs["timeout"] == 60


def test_extract_raises_on_zero_assertions():
    # ADI-011: 0 extracted assertions is a failure, not a successful empty result.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response("")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "0 assertions" in str(exc_info.value)


def test_extract_raises_on_zero_output_includes_done_reason():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response("", done_reason="length")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "done_reason='length'" in str(exc_info.value)


def test_extract_raises_on_invalid_epistemic_status():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response("certainly: A fact.")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "Invalid epistemic_status" in str(exc_info.value)


def test_extract_wraps_http_error():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = ConnectionError("connection refused")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "Failed to extract" in str(exc_info.value)


def test_missing_requests_dependency_raises_import_error(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("no requests")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError):
        OllamaProvider(OllamaProviderConfig())
