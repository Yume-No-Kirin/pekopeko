"""
OllamaProvider unit tests: prompt building and JSON response parsing.
No real network calls - requests.post is mocked (project rule: the LLM
provider must be mocked/faked in tests).
"""
import json
from unittest.mock import Mock

import pytest

from _helpers import REPO_ROOT  # noqa: F401

from src.app.extraction.providers.ollama_provider import (
    FALLBACK_PATH_SEGMENTS,
    PATH_PROPOSAL_MAX_ATTEMPTS,
    OllamaProvider,
    OllamaProviderConfig,
    _normalize_path_string,
)
from src.app.extraction.providers.base import ExtractionResult


def _mock_response(payload: dict, done_reason: str = None):
    response = Mock()
    response.raise_for_status = Mock()
    response_json = {"response": json.dumps(payload)}
    if done_reason is not None:
        response_json["done_reason"] = done_reason
    response.json.return_value = response_json
    return response


def _mock_path_response(text: str):
    """A path-proposal call's response: the model's raw text reply is a plain
    path string, unlike the main extraction call's JSON-object response."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {"response": text}
    return response


def test_extract_parses_full_json_response():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    # 1 main extraction call + 1 path-proposal call per non-empty type
    # (entities/events/relationships all non-empty here - TASK-005a).
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
            "events": [{"local_id": "ev1", "text": "A talk", "epistemic_status": "inferred", "starts_at": None, "ends_at": None}],
            "relationships": [{"text": "Ada gave the talk", "epistemic_status": "direct", "relationship_type": "gave", "endpoints": ["e1", "ev1"]}],
        }),
        _mock_path_response("personnages"),
        _mock_path_response("evenements"),
        _mock_path_response("relations"),
    ]

    result = provider.extract("some source text", {"source_path": "test.md"})

    assert isinstance(result, ExtractionResult)
    assert len(result.entities) == 1
    assert result.entities[0].local_id == "e1"
    assert len(result.events) == 1
    assert len(result.relationships) == 1
    assert result.relationships[0].endpoints == ["e1", "ev1"]

    assert provider.requests.post.call_count == 4
    first_call_kwargs = provider.requests.post.call_args_list[0].kwargs
    assert first_call_kwargs["json"]["model"] == "llama3"
    assert first_call_kwargs["timeout"] == 60


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


# TASK-005a: ADI-012 adoption by entity/event/relationship - mandatory,
# per-note-per-type folder-path proposal (mirrors ingestion's ADI-014/015
# machinery, independently reimplemented - no import from ingestion/).

def test_extract_issues_exactly_one_path_proposal_call_per_non_empty_type():
    """AC8: entities+events+relationships all non-empty -> exactly 3 path-proposal
    calls (not one per item), regardless of how many items each type has."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [
                {"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"},
                {"local_id": "e2", "entity_type": "person", "text": "Charles", "epistemic_status": "direct"},
            ],
            "events": [
                {"local_id": "ev1", "text": "A talk", "epistemic_status": "direct", "starts_at": None, "ends_at": None},
            ],
            "relationships": [
                {"text": "Ada knows Charles", "epistemic_status": "direct", "relationship_type": "knows", "endpoints": ["e1", "e2"]},
            ],
        }),
        _mock_path_response("personnages"),
        _mock_path_response("evenements"),
        _mock_path_response("relations"),
    ]

    provider.extract("source text", {"source_path": "test.md"})

    assert provider.requests.post.call_count == 4


def test_extract_same_type_shares_path_independent_types_resolved_independently():
    """AC9: every item of a given type carries the same proposed_path_segments;
    the three types carry independently resolved values."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [
                {"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"},
                {"local_id": "e2", "entity_type": "person", "text": "Charles", "epistemic_status": "direct"},
            ],
            "events": [
                {"local_id": "ev1", "text": "A talk", "epistemic_status": "direct", "starts_at": None, "ends_at": None},
                {"local_id": "ev2", "text": "A meeting", "epistemic_status": "direct", "starts_at": None, "ends_at": None},
            ],
        }),
        _mock_path_response("personnages"),
        _mock_path_response("evenements"),
    ]

    result = provider.extract("source text", {"source_path": "test.md"})

    assert result.entities[0].proposed_path_segments == ["personnages"]
    assert result.entities[1].proposed_path_segments == ["personnages"]
    assert result.events[0].proposed_path_segments == ["evenements"]
    assert result.events[1].proposed_path_segments == ["evenements"]
    assert result.entities[0].proposed_path_segments != result.events[0].proposed_path_segments


def test_extract_zero_items_of_a_type_triggers_no_path_proposal_call():
    """AC10: entities+events non-empty, relationships empty -> only 2 path-proposal
    calls (relationships triggers none)."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
            "events": [{"local_id": "ev1", "text": "A talk", "epistemic_status": "direct", "starts_at": None, "ends_at": None}],
        }),
        _mock_path_response("personnages"),
        _mock_path_response("evenements"),
    ]

    result = provider.extract("source text", {"source_path": "test.md"})

    assert result.relationships == []
    # 1 extraction call + 2 path-proposal calls (entity, event) - none for relationship.
    assert provider.requests.post.call_count == 3


def test_path_proposal_falls_back_after_exhausting_retries():
    """AC11: when the path call keeps returning unusable output, items of that
    type end up with FALLBACK_PATH_SEGMENTS after exactly PATH_PROPOSAL_MAX_ATTEMPTS
    attempts, and extraction still completes successfully."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
        }),
        # Every path-proposal attempt returns something that normalizes to [] -
        # a lone connector word, dropped by _normalize_path_string's stopword set.
        _mock_path_response("de"),
        _mock_path_response("de"),
        _mock_path_response("de"),
    ]

    result = provider.extract("source text", {"source_path": "test.md"})

    assert result.entities[0].proposed_path_segments == FALLBACK_PATH_SEGMENTS
    assert provider.requests.post.call_count == 1 + PATH_PROPOSAL_MAX_ATTEMPTS


def test_path_proposal_swallows_errors_during_retry_then_falls_back():
    """A network/HTTP error during a path-proposal attempt counts as a failed
    attempt and is retried silently, same posture as ingestion's own provider."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
        }),
        ConnectionError("connection refused"),
        ConnectionError("connection refused"),
        ConnectionError("connection refused"),
    ]

    result = provider.extract("source text", {"source_path": "test.md"})

    assert result.entities[0].proposed_path_segments == FALLBACK_PATH_SEGMENTS


def test_path_proposal_retries_then_succeeds():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
        }),
        _mock_path_response("de"),  # normalizes to [] - counts as a failed attempt
        _mock_path_response("personnages"),  # succeeds on the 2nd attempt
    ]

    result = provider.extract("source text", {"source_path": "test.md"})

    assert result.entities[0].proposed_path_segments == ["personnages"]
    assert provider.requests.post.call_count == 3


def test_extract_merges_accepted_and_pending_folders_when_vault_root_and_domain_present(tmp_path):
    """AC14: when context carries vault_root/domain, existing_folders is built from
    scan_existing_item_folders (accepted) + scan_proposed_path_segments (pending),
    scoped to the resolving type."""
    vault_root = tmp_path / "vault"
    (vault_root / "PERSONAL" / "entities" / "lieux" / "entity-1").mkdir(parents=True)
    proposal_dir = vault_root / "PERSONAL" / "proposals" / "prop-1"
    proposal_dir.mkdir(parents=True)
    (proposal_dir / "prop-1.md").write_text(
        "---\nproposal_status: PROPOSED\nproposed_item_type: entity\n"
        "proposed_path_segments:\n- personnages\n---\n\nBody.",
        encoding="utf-8",
    )

    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada", "epistemic_status": "direct"}],
        }),
        _mock_path_response("lieux"),
    ]

    provider.extract("source text", {"source_path": "test.md", "vault_root": str(vault_root), "domain": "PERSONAL"})

    path_call_prompt = provider.requests.post.call_args_list[1].kwargs["json"]["prompt"]
    assert "lieux" in path_call_prompt
    assert "personnages" in path_call_prompt


def test_extract_passes_source_text_and_item_texts_into_path_prompt():
    """_build_path_prompt names the plural type and lists every item's text -
    confirmed by inspecting the actual prompt sent."""
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response({
            "entities": [{"local_id": "e1", "entity_type": "person", "text": "Ada Lovelace", "epistemic_status": "direct"}],
        }),
        _mock_path_response("personnages"),
    ]

    provider.extract("Full source note content here.", {"source_path": "test.md"})

    path_call_prompt = provider.requests.post.call_args_list[1].kwargs["json"]["prompt"]
    assert "Full source note content here." in path_call_prompt
    assert "Ada Lovelace" in path_call_prompt
    assert "entities" in path_call_prompt


# _normalize_path_string: independently reimplemented from ingestion's, must
# yield the same clean segments for the same dirty input (AC12, ADI-015 worked
# examples - test bodies mirror src/tests/ingestion/test_ollama_provider.py's
# own _normalize_path_string suite exactly).

def test_normalize_path_string_strips_accents():
    assert _normalize_path_string("système/tatouages") == ["systeme", "tatouages"]


def test_normalize_path_string_strips_ligatures():
    assert _normalize_path_string("œuvre/sœur") == ["oeuvre", "soeur"]


def test_normalize_path_string_unescapes_html_entities():
    assert _normalize_path_string("enjeux / &amp;themes") == ["enjeux", "themes"]


def test_normalize_path_string_splits_ampersand_into_separate_segments():
    assert _normalize_path_string("enjeux&themes") == ["enjeux", "themes"]


def test_normalize_path_string_splits_vs_into_separate_segments():
    assert _normalize_path_string("symbiose-vs-domination") == ["symbiose", "domination"]


def test_normalize_path_string_splits_underscore_and_hyphen_compounds():
    assert _normalize_path_string("ecologie_anti_colonialisme") == ["ecologie", "anti", "colonialisme"]
    assert _normalize_path_string("coopération_vs_pouvoir_solitaire") == [
        "cooperation", "pouvoir", "solitaire"
    ]


def test_normalize_path_string_drops_grammatical_stopwords():
    assert _normalize_path_string("conflit/de/pouvoir") == ["conflit", "pouvoir"]


def test_normalize_path_string_lowercases_and_strips_special_characters():
    assert _normalize_path_string("Conflict/Moral!/Social?") == ["conflict", "moral", "social"]


def test_normalize_path_string_real_dirty_examples_from_production():
    # Same exact strings ingestion's own suite checks (ADI-015) - the two
    # implementations must agree on the same input.
    assert _normalize_path_string("enjeux / &amp;thèmes / ecologie_anti_colonialisme") == [
        "enjeux", "themes", "ecologie", "anti", "colonialisme"
    ]
