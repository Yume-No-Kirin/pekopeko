"""
TASK-003a: extraction-produced proposals must carry top-level `id`/`type`
fields matching the shape review/ (and ingestion/'s assertion proposals)
already require, so review/'s generic proposal validation can see them.
"""
from _helpers import read_frontmatter

from src.app.extraction import storage
from src.app.extraction.errors import ValidationError
from src.app.extraction.providers.base import ExtractedEntity, ExtractedEvent, ExtractedRelationship
from src.app.review import storage as review_storage


def _proposal_frontmatter(vault_root, domain, proposal_id):
    path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"
    fm, _ = read_frontmatter(path)
    return fm


def test_entity_proposal_has_id_and_type(tmp_path):
    vault_root = tmp_path / "vault"
    entity = ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")
    proposal_id = storage.write_entity_proposal_file(vault_root, "PERSONAL", entity, "src-abc", "TestProvider")

    fm = _proposal_frontmatter(vault_root, "PERSONAL", proposal_id)
    assert fm["id"] == proposal_id
    assert fm["type"] == "proposal"


def test_event_proposal_has_id_and_type(tmp_path):
    vault_root = tmp_path / "vault"
    event = ExtractedEvent(local_id="ev1", text="An event", epistemic_status="direct", starts_at=None, ends_at=None)
    proposal_id = storage.write_event_proposal_file(vault_root, "PERSONAL", event, "src-abc", "TestProvider")

    fm = _proposal_frontmatter(vault_root, "PERSONAL", proposal_id)
    assert fm["id"] == proposal_id
    assert fm["type"] == "proposal"


def test_relationship_proposal_has_id_and_type(tmp_path):
    vault_root = tmp_path / "vault"
    relationship = ExtractedRelationship(
        text="Ada attended the lecture", epistemic_status="direct",
        relationship_type="attended", endpoints=["a", "b"],
    )
    proposal_id = storage.write_relationship_proposal_file(
        vault_root, "PERSONAL", relationship, ["a", "b"], "src-abc", "TestProvider"
    )

    fm = _proposal_frontmatter(vault_root, "PERSONAL", proposal_id)
    assert fm["id"] == proposal_id
    assert fm["type"] == "proposal"


def test_required_proposal_fields_includes_id_and_type():
    assert "id" in storage.REQUIRED_PROPOSAL_FIELDS
    assert "type" in storage.REQUIRED_PROPOSAL_FIELDS


def test_validate_frontmatter_reports_missing_id_and_type():
    frontmatter = {
        "item_type": "proposal", "domain": "PERSONAL", "created_at": "now",
        "proposal_status": "PROPOSED", "provenance": {}, "proposed_item_type": "entity",
        "epistemic_status": "direct", "valid_from": "now", "valid_until": None,
    }
    try:
        storage._validate_frontmatter(frontmatter, storage.REQUIRED_PROPOSAL_FIELDS)
        assert False, "expected ValidationError"
    except ValidationError as exc:
        assert "id" in str(exc)
        assert "type" in str(exc)


def test_entity_proposal_passes_reviews_own_required_fields_validation(tmp_path):
    """AC3: review/'s real validation helper, run directly against a proposal
    this ticket's writers produce, must no longer fail on missing id/type."""
    vault_root = tmp_path / "vault"
    entity = ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")
    proposal_id = storage.write_entity_proposal_file(vault_root, "PERSONAL", entity, "src-abc", "TestProvider")

    fm = _proposal_frontmatter(vault_root, "PERSONAL", proposal_id)
    review_storage._validate_frontmatter(fm, review_storage.REQUIRED_PROPOSAL_FIELDS)


def test_pre_existing_fields_unchanged(tmp_path):
    """AC4: no regression to fields already written before this ticket."""
    vault_root = tmp_path / "vault"
    entity = ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct")
    proposal_id = storage.write_entity_proposal_file(vault_root, "PERSONAL", entity, "src-abc", "TestProvider")

    fm = _proposal_frontmatter(vault_root, "PERSONAL", proposal_id)
    assert fm["item_type"] == "proposal"
    assert fm["domain"] == "PERSONAL"
    assert fm["proposal_status"] == "PROPOSED"
    assert fm["proposed_item_type"] == "entity"
    assert fm["epistemic_status"] == "direct"
    assert fm["entity_type"] == "person"
    assert fm["provenance"] == {"source_id": "src-abc", "extraction_provider": "TestProvider"}
