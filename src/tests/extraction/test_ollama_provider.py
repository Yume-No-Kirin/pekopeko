"""
OllamaProvider unit tests: prompt building and JSON response parsing.
No real network calls - requests.post is mocked (project rule: the LLM
provider must be mocked/faked in tests).
"""
import json
from unittest.mock import Mock

import pytest

from _helpers import REPO_ROOT  # noqa: F401

from src.app.extraction.providers.ollama_provider import OllamaProvider, OllamaProviderConfig
from src.app.extraction.providers.base import ExtractionResult


def _mock_response(payload: dict, done_reason: str = None):
    response = Mock()
    response.raise_for_status = Mock()
    response_json = {"response": json.dumps(payload)}
    if done_reason is not None:
        response_json["done_reason"] = done_reason
    response.json.return_value = response_json
    return response


def test_extract_parses_full_json_response():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response({
        "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
        "events": [{"local_id": "ev1", "text": "A talk", "epistemic_status": "inferred", "starts_at": None, "ends_at": None}],
        "relationships": [{"text": "Ada gave the talk", "epistemic_status": "direct", "relationship_type": "gave", "endpoints": ["e1", "ev1"]}],
    })

    result = provider.extract("some source text", {"source_path": "test.md"})

    assert isinstance(result, ExtractionResult)
    assert len(result.entities) == 1
    assert result.entities[0].local_id == "e1"
    assert len(result.events) == 1
    assert len(result.relationships) == 1
    assert result.relationships[0].endpoints == ["e1", "ev1"]

    provider.requests.post.assert_called_once()
    call_kwargs = provider.requests.post.call_args.kwargs
    assert call_kwargs["json"]["model"] == "llama3"
    assert call_kwargs["timeout"] == 60


def test_extract_raises_on_all_empty_lists():
    # ADI-011: 0 extracted items is a failure, not a successful empty result.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response({})

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "0 entities/events/relationships" in str(exc_info.value)


def test_extract_raises_on_zero_output_includes_done_reason():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response({}, done_reason="length")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "done_reason='length'" in str(exc_info.value)


def test_extract_raises_on_empty_response_text_before_json_parse():
    # The real gpt-oss:20b incident: response body is "" with done_reason
    # "length" - must raise (with done_reason surfaced) before ever
    # attempting JSON parsing, rather than falling through to the unrelated
    # "did not contain a JSON object" error.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"response": "", "done_reason": "length"}
    provider.requests.post.return_value = response

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "0 entities/events/relationships" in str(exc_info.value)
    assert "done_reason='length'" in str(exc_info.value)


def test_extract_succeeds_when_at_least_one_list_non_empty():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response({
        "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
    })

    result = provider.extract("text", {})

    assert len(result.entities) == 1
    assert result.events == []
    assert result.relationships == []


def test_extract_raises_on_invalid_epistemic_status():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response({
        "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "certainly"}],
    })

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "Invalid epistemic_status" in str(exc_info.value)


def test_extract_raises_on_malformed_json():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"response": "not json at all, no braces"}
    provider.requests.post.return_value = response

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "JSON" in str(exc_info.value)


def test_extract_raises_on_invalid_json_inside_braces():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"response": "{not: valid, json}"}
    provider.requests.post.return_value = response

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "not valid JSON" in str(exc_info.value)


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
