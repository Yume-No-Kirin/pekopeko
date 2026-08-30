"""
Type-specific proposal fields per proposed_item_type (AC1), and relationship
endpoint resolution from local_id to proposal_id.
"""
from _helpers import read_frontmatter

from src.app.extraction import (
    extract_source,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractionResult,
)
from src.app.extraction.errors import ValidationError
from src.app.extraction import storage


class FakeProvider:
    def __init__(self, result: ExtractionResult):
        self.result = result

    def extract(self, text, context):
        return self.result


def _proposal_frontmatter(vault_root, domain, proposal_id):
    path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"
    fm, _ = read_frontmatter(path)
    return fm


def test_entity_type_field_present(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("Ada Lovelace was a mathematician.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    provider = FakeProvider(ExtractionResult(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")],
    ))
    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=tmp_path / "state")

    assert result.status == "completed"
    fm = _proposal_frontmatter(vault_root, "PERSONAL", result.proposal_ids[0])
    assert fm["proposed_item_type"] == "entity"
    assert fm["entity_type"] == "person"
    assert "starts_at" not in fm
    assert "relationship_type" not in fm


def test_event_starts_ends_at_present(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("Ada met Babbage in 1833.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    provider = FakeProvider(ExtractionResult(
        events=[ExtractedEvent(
            local_id="ev1", text="Met Babbage", epistemic_status="inferred",
            starts_at="1833-06-01T00:00:00", ends_at=None,
        )],
    ))
    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=tmp_path / "state")

    assert result.status == "completed"
    fm = _proposal_frontmatter(vault_root, "PERSONAL", result.proposal_ids[0])
    assert fm["proposed_item_type"] == "event"
    assert fm["starts_at"] == "1833-06-01T00:00:00"
    assert fm["ends_at"] is None
    assert "entity_type" not in fm


def test_relationship_type_and_endpoints_present_and_resolved(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("Ada attended a lecture by Babbage.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    provider = FakeProvider(ExtractionResult(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")],
        events=[ExtractedEvent(local_id="ev1", text="A lecture", epistemic_status="direct")],
        relationships=[ExtractedRelationship(
            text="Ada attended the lecture", epistemic_status="direct",
            relationship_type="attended", endpoints=["e1", "ev1"],
        )],
    ))
    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=tmp_path / "state")

    assert result.status == "completed"
    assert len(result.proposal_ids) == 3

    entity_id, event_id, relationship_id = result.proposal_ids
    rel_fm = _proposal_frontmatter(vault_root, "PERSONAL", relationship_id)
    assert rel_fm["proposed_item_type"] == "relationship"
    assert rel_fm["relationship_type"] == "attended"
    # local_id references ("e1", "ev1") must be resolved to the real proposal_ids.
    assert rel_fm["endpoints"] == [entity_id, event_id]
    assert "entity_type" not in rel_fm
    assert "starts_at" not in rel_fm


def test_relationship_endpoint_referencing_existing_canonical_id_passed_through(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("Ada attended a lecture at an existing venue.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    provider = FakeProvider(ExtractionResult(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")],
        relationships=[ExtractedRelationship(
            text="Ada attended at an existing venue", epistemic_status="direct",
            relationship_type="attended_at", endpoints=["e1", "entity-existing-venue-123"],
        )],
    ))
    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=tmp_path / "state")

    assert result.status == "completed"
    entity_id, relationship_id = result.proposal_ids
    rel_fm = _proposal_frontmatter(vault_root, "PERSONAL", relationship_id)
    # "entity-existing-venue-123" does not match any local_id from this
    # extraction, so it is passed through unchanged (existing canonical id).
    assert rel_fm["endpoints"] == [entity_id, "entity-existing-venue-123"]


def test_relationship_endpoints_fewer_than_two_raises_before_write(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("Something happened.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    provider = FakeProvider(ExtractionResult(
        relationships=[ExtractedRelationship(
            text="lonely relationship", epistemic_status="direct",
            relationship_type="mysterious", endpoints=["only-one"],
        )],
    ))
    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=tmp_path / "state")

    assert result.status == "failed"
    assert result.error is not None
    assert not (vault_root / "PERSONAL" / "proposals").exists() or \
        len(list((vault_root / "PERSONAL" / "proposals").iterdir())) == 0


def test_storage_rejects_endpoints_directly():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir)
        relationship = ExtractedRelationship(
            text="x", epistemic_status="direct", relationship_type="y", endpoints=["only-one"],
        )
        try:
            storage.write_relationship_proposal_file(
                vault_root, "PERSONAL", relationship, ["only-one"], "src-abc", "TestProvider"
            )
            assert False, "expected ValidationError"
        except ValidationError:
            pass
