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

from src.app.ingestion.providers.ollama_provider import (
    OllamaProvider, OllamaProviderConfig, _normalize_path_string
)
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
    # Neither line carries an inline "| <path>" suffix, so a path-proposal call
    # fires for each assertion (mandatory path, 2026-09-04 amendment to TASK-001e).
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue.\ninferred: It rained recently."),
        _mock_response("weather/observations"),
        _mock_response("weather/rain"),
    ]

    result = provider.extract("some source text", {"source_path": "test.md"})

    assert isinstance(result, ExtractionResult)
    assert len(result.assertions) == 2
    assert result.assertions[0].epistemic_status == "direct"
    assert result.assertions[1].epistemic_status == "inferred"
    assert result.assertions[0].proposed_path_segments == ["weather", "observations"]
    assert result.assertions[1].proposed_path_segments == ["weather", "rain"]

    assert provider.requests.post.call_count == 3
    call_kwargs = provider.requests.post.call_args_list[0].kwargs
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


def test_extract_parses_proposed_path_segments():
    # TASK-001e AC3: a valid "| <path>" suffix produces the slash-split, trimmed segments.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response(
        "direct: The author published this book in 2023. | mythologie / japonaise/kitsune"
    )

    result = provider.extract("some source text", {})

    assert result.assertions[0].proposed_path_segments == ["mythologie", "japonaise", "kitsune"]


def test_extract_no_path_suffix_triggers_path_proposal_call():
    # Amends TASK-001e AC4 (2026-09-04, Cleo): a missing "|" suffix used to leave
    # proposed_path_segments == [] (optional field). The path is now mandatory - a
    # missing suffix instead triggers a dedicated per-assertion path-proposal call.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue."),
        _mock_response("meteorologie/observations"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["meteorologie", "observations"]
    assert provider.requests.post.call_count == 2
    second_call_prompt = provider.requests.post.call_args_list[1].kwargs["json"]["prompt"]
    assert "The sky is blue." in second_call_prompt
    assert "(none yet)" in second_call_prompt  # no vault_root/domain in context


def test_extract_empty_path_suffix_triggers_path_proposal_call():
    # Amends TASK-001e AC5 (2026-09-04): an empty/whitespace-only "|" suffix used to
    # yield [] directly; it now also triggers the mandatory path-proposal call.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue. |   "),
        _mock_response("meteorologie/observations"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["meteorologie", "observations"]
    assert provider.requests.post.call_count == 2


def test_extract_only_calls_path_proposal_for_assertions_missing_one():
    # Mixed batch: the first line already has an inline path, the second doesn't -
    # only the second triggers a path-proposal call.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response(
            "direct: Has a path. | mythologie/japonaise\ninferred: Missing a path."
        ),
        _mock_response("meteorologie/observations"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["mythologie", "japonaise"]
    assert result.assertions[1].proposed_path_segments == ["meteorologie", "observations"]
    assert provider.requests.post.call_count == 2


def test_path_proposal_retries_then_succeeds():
    # A blank first response doesn't count as a valid path - retried until one lands.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue."),
        _mock_response(""),
        _mock_response("meteorologie/observations"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["meteorologie", "observations"]
    assert provider.requests.post.call_count == 3


def test_path_proposal_falls_back_after_exhausting_retries():
    # All PATH_PROPOSAL_MAX_ATTEMPTS (3) attempts come back empty -> fallback segments.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue."),
        _mock_response(""),
        _mock_response("   "),
        _mock_response(""),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["uncategorized"]
    assert provider.requests.post.call_count == 4


def test_path_proposal_swallows_errors_during_retry_then_falls_back():
    # A network/HTTP error on a path-proposal attempt is retried, not raised - the
    # user's explicit choice (retry-then-fallback, not a hard failure of the task).
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: The sky is blue."),
        ConnectionError("boom"),
        ConnectionError("boom"),
        ConnectionError("boom"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["uncategorized"]


def test_extract_passes_existing_vault_folders_to_path_prompt(tmp_path):
    vault_root = tmp_path / "vault"
    (vault_root / "FICTION" / "assertions" / "mythologie" / "japonaise").mkdir(parents=True)

    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: A fact."),
        _mock_response("mythologie/japonaise"),
    ]

    provider.extract("text", {"vault_root": str(vault_root), "domain": "FICTION"})

    second_call_prompt = provider.requests.post.call_args_list[1].kwargs["json"]["prompt"]
    assert "mythologie/japonaise" in second_call_prompt
    assert "(none yet)" not in second_call_prompt


def test_extract_merges_accepted_and_pending_proposal_folders_into_context(tmp_path):
    # ADI-015: existing_folders is the union of the canonical accepted tree
    # (scan_existing_assertion_folders) and not-yet-accepted Proposals'
    # proposed_path_segments (scan_proposed_path_segments).
    import yaml

    vault_root = tmp_path / "vault"
    (vault_root / "FICTION" / "assertions" / "geographie").mkdir(parents=True)

    proposal_dir = vault_root / "FICTION" / "proposals" / "prop-1"
    proposal_dir.mkdir(parents=True)
    frontmatter = yaml.dump(
        {"proposal_status": "PROPOSED", "proposed_path_segments": ["mythologie", "kitsune"]},
        default_flow_style=False,
    )
    (proposal_dir / "prop-1.md").write_text(f"---\n{frontmatter}---\n\nBody.", encoding="utf-8")

    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: A fact."),
        _mock_response("geographie"),
    ]

    provider.extract("text", {"vault_root": str(vault_root), "domain": "FICTION"})

    second_call_prompt = provider.requests.post.call_args_list[1].kwargs["json"]["prompt"]
    assert "geographie" in second_call_prompt
    assert "mythologie/kitsune" in second_call_prompt


def test_extract_malformed_path_suffix_drops_empty_segments():
    # TASK-001e AC6: leading/trailing/doubled slashes never raise; empty segments dropped,
    # non-empty ones kept in order.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response(
        "direct: The sky is blue. | /a//b/"
    )

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["a", "b"]


def test_extract_raises_on_invalid_epistemic_status_with_path_suffix():
    # TASK-001e AC7: presence of a "|" suffix doesn't bypass epistemic_status validation.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response("certainly: A fact. | some/path")

    with pytest.raises(Exception) as exc_info:
        provider.extract("text", {})
    assert "Invalid epistemic_status" in str(exc_info.value)


def test_build_extraction_prompt_includes_path_suffix_instruction():
    # TASK-001e AC2: the prompt sent to Ollama documents the optional "| <path>" suffix.
    provider = OllamaProvider(OllamaProviderConfig())

    prompt = provider._build_extraction_prompt("some text", {})

    assert "| <segment1>/<segment2>/..." in prompt
    assert "mythologie/japonaise/kitsune" in prompt


def test_build_extraction_prompt_includes_nomenclature_rules():
    # ADI-015 (amends ADI-014): the prompt documents the one-word/no-accent/
    # no-joined-concepts nomenclature, with a worked before/after example.
    provider = OllamaProvider(OllamaProviderConfig())

    prompt = provider._build_extraction_prompt("some text", {})

    assert "no accents" in prompt
    assert "Never join two ideas into one segment" in prompt
    assert "intrigue/mission/conflit/escalation" in prompt


def test_build_path_prompt_includes_nomenclature_rules():
    provider = OllamaProvider(OllamaProviderConfig())

    prompt = provider._build_path_prompt("Some assertion.", "Some source text.", [])

    assert "no accents" in prompt
    assert "Never join two ideas into one segment" in prompt
    assert "intrigue/mission/conflit/escalation" in prompt


# --- _normalize_path_string (ADI-015: deterministic nomenclature safety net) ---

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
    # Exact strings observed in a real Cleo screenshot before this amendment.
    assert _normalize_path_string("enjeux / &amp;thèmes / ecologie_anti_colonialisme") == [
        "enjeux", "themes", "ecologie", "anti", "colonialisme"
    ]
    assert _normalize_path_string("conflits / coopération_vs_pouvoir_solitaire") == [
        "conflits", "cooperation", "pouvoir", "solitaire"
    ]
    assert _normalize_path_string("symbiose-vs-domination") == ["symbiose", "domination"]
    assert _normalize_path_string("enjeux_thematiques / systeme_economique_militaire") == [
        "enjeux", "thematiques", "systeme", "economique", "militaire"
    ]


def test_extract_applies_normalization_to_inline_suffix():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.return_value = _mock_response(
        "direct: Fact. | système/tatouages&rituels"
    )

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["systeme", "tatouages", "rituels"]


def test_extract_applies_normalization_to_second_call_response():
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: Fact."),
        _mock_response("Système / Tatouages&Rituels"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["systeme", "tatouages", "rituels"]


def test_extract_within_batch_reuses_earlier_assertions_path_as_context():
    # A later assertion in the same batch should see the path an earlier assertion in
    # the SAME extraction call already chose, before anything is written to disk.
    provider = OllamaProvider(OllamaProviderConfig())
    provider.requests = Mock()
    provider.requests.post.side_effect = [
        _mock_response("direct: First fact.\ninferred: Second fact."),
        _mock_response("mythologie/kitsune"),
        _mock_response("mythologie/kitsune"),
    ]

    result = provider.extract("text", {})

    assert result.assertions[0].proposed_path_segments == ["mythologie", "kitsune"]
    assert result.assertions[1].proposed_path_segments == ["mythologie", "kitsune"]

    second_assertion_prompt = provider.requests.post.call_args_list[2].kwargs["json"]["prompt"]
    assert "mythologie/kitsune" in second_assertion_prompt
    assert "(none yet)" not in second_assertion_prompt


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
