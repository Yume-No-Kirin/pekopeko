"""
Unit tests for the extraction pipeline: first-extraction contract (AC1),
duplicate detection (AC3), provider failure handling (AC4), domain
validation.
"""
from pathlib import Path
from unittest.mock import Mock

import pytest

from _helpers import read_frontmatter

from src.app.extraction import (
    extract_source,
    ExtractionPipelineResult,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractionResult,
)
from src.app.extraction.errors import InvalidDomainError


class FakeProvider:
    def __init__(self, result: ExtractionResult):
        self.result = result
        self.calls = 0

    def extract(self, text: str, context: dict) -> ExtractionResult:
        self.calls += 1
        return self.result


def _full_extraction_result() -> ExtractionResult:
    return ExtractionResult(
        entities=[
            ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct"),
        ],
        events=[
            ExtractedEvent(
                local_id="ev1", text="Met Babbage", epistemic_status="inferred",
                starts_at="1833-06-01T00:00:00", ends_at=None,
            ),
        ],
        relationships=[
            ExtractedRelationship(
                text="Ada attended the event", epistemic_status="direct",
                relationship_type="participated_in", endpoints=["e1", "ev1"],
            ),
        ],
    )


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("# Test Document\n\nAda Lovelace met Charles Babbage in 1833.", encoding="utf-8")
    return path


def test_first_extraction_full_contract(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert isinstance(result, ExtractionPipelineResult)
    assert result.status == "completed"
    assert result.skipped_duplicate is False
    assert result.source_id is not None
    assert len(result.proposal_ids) == 3

    source_path = vault_root / "PERSONAL" / "sources" / result.source_id / f"{result.source_id}.md"
    assert source_path.exists()
    source_fm, source_body = read_frontmatter(source_path)
    assert source_fm["item_type"] == "source"
    assert source_fm["domain"] == "PERSONAL"
    assert source_fm["source_id"] == result.source_id
    assert source_fm["source_format"] == "markdown"
    assert source_fm["created_at"]
    assert source_fm["source_path"] == f"PERSONAL/sources/{result.source_id}/{result.source_id}.md"
    assert "Ada Lovelace met Charles Babbage" in source_fm["content"]

    for proposal_id in result.proposal_ids:
        proposal_path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
        assert proposal_path.exists()
        fm, _ = read_frontmatter(proposal_path)
        assert fm["item_type"] == "proposal"
        assert fm["domain"] == "PERSONAL"
        assert fm["proposal_status"] == "PROPOSED"
        assert fm["provenance"]["source_id"] == result.source_id
        assert fm["provenance"]["extraction_provider"] == "FakeProvider"
        assert fm["proposed_item_type"] in {"entity", "event", "relationship"}
        assert fm["epistemic_status"] in {"direct", "inferred", "uncertain", "contested"}
        assert "valid_from" in fm
        assert "valid_until" in fm


def test_duplicate_detection(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result1 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result1.status == "completed"
    assert provider.calls == 1

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "skipped_duplicate"
    assert result2.skipped_duplicate is True
    assert result2.source_id == result1.source_id
    assert result2.proposal_ids == []
    # No second call to the provider for a duplicate.
    assert provider.calls == 1

    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert len(list(proposals_dir.iterdir())) == 3


def test_provider_failure_handling(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = Mock()
    provider.extract.side_effect = Exception("provider exploded")

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert result.error is not None
    assert "provider exploded" in result.error

    # Source file was written before the provider call and is left in place,
    # untouched/uncorrupted - it is a complete write, not a partial one.
    source_path = vault_root / "PERSONAL" / "sources" / result.source_id / f"{result.source_id}.md"
    assert source_path.exists()

    # No proposal files were written.
    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert not proposals_dir.exists() or len(list(proposals_dir.iterdir())) == 0

    # The original input file is untouched.
    assert "Ada Lovelace" in source_file.read_text(encoding="utf-8")


def test_domain_validation(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    with pytest.raises(InvalidDomainError):
        extract_source(vault_root, "NOT_A_DOMAIN", source_file, provider, state_dir=state_dir)

    assert not vault_root.exists()


def test_default_state_dir_used_when_not_provided(tmp_path, source_file, monkeypatch):
    # Monkeypatch the module-level default so this never touches the real
    # home directory (AGENTS.md: tests must never write outside their own
    # temp directory).
    from src.app.extraction import pipeline as pipeline_module

    fake_default = tmp_path / "fake_home_state"
    monkeypatch.setattr(pipeline_module, "DEFAULT_STATE_DIR", fake_default)

    vault_root = tmp_path / "vault"
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", source_file, provider)

    assert result.status == "completed"
    assert fake_default.exists()
    assert list(fake_default.glob("extract-*.json"))


def test_unregistered_extension_fails_via_outer_handler(tmp_path):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    unsupported_file = tmp_path / "test.pdf"
    unsupported_file.write_text("not markdown", encoding="utf-8")
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", unsupported_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert "No reader registered" in result.error
    assert not vault_root.exists()
