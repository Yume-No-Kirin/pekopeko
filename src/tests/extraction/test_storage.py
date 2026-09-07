"""
storage.py unit tests: atomic writes (AC8), frontmatter/domain validation.
"""
import os
from pathlib import Path

import pytest
import yaml

from _helpers import read_frontmatter

from src.app.extraction import storage
from src.app.extraction.errors import InvalidDomainError, ValidationError
from src.app.extraction.providers.base import ExtractedEntity, ExtractedEvent, ExtractedRelationship


def test_write_source_file_creates_expected_layout(tmp_path):
    vault_root = tmp_path / "vault"
    source_id = storage.write_source_file(vault_root, "PERSONAL", "hello world")

    path = vault_root / "PERSONAL" / "sources" / source_id / f"{source_id}.md"
    assert path.exists()
    fm, body = read_frontmatter(path)
    assert fm["item_type"] == "source"
    assert fm["source_id"] == source_id
    assert body == "hello world"


def test_write_source_file_deterministic_id_from_content(tmp_path):
    vault_root = tmp_path / "vault"
    id1 = storage.write_source_file(vault_root, "PERSONAL", "same content")
    id2 = storage._generate_source_id("same content")
    assert id1 == id2


def test_source_id_changes_when_middle_of_content_changes():
    # Demonstrates the hash covers the *entire* content, not just a prefix
    # or suffix: two long strings sharing the same first and last 16
    # characters, differing only in the middle, must still get different ids.
    prefix = "A" * 16
    suffix = "B" * 16
    content_a = f"{prefix}-original-middle-section-{suffix}"
    content_b = f"{prefix}-different-middle-section-{suffix}"
    assert content_a[:16] == content_b[:16]
    assert content_a[-16:] == content_b[-16:]

    assert storage._generate_source_id(content_a) != storage._generate_source_id(content_b)


def test_source_id_stable_for_identical_full_content():
    long_content = "x" * 10_000 + "unique marker" + "y" * 10_000
    assert storage._generate_source_id(long_content) == storage._generate_source_id(long_content)


def test_write_source_file_invalid_domain_raises(tmp_path):
    vault_root = tmp_path / "vault"
    with pytest.raises(InvalidDomainError):
        storage.write_source_file(vault_root, "NOT_A_DOMAIN", "content")
    assert not vault_root.exists()


def test_write_entity_proposal_file_invalid_epistemic_status_raises(tmp_path):
    vault_root = tmp_path / "vault"
    entity = ExtractedEntity(local_id="e1", entity_type="person", text="x", epistemic_status="definitely_true")
    with pytest.raises(ValidationError):
        storage.write_entity_proposal_file(vault_root, "PERSONAL", entity, "src-abc", "TestProvider")
    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert not proposals_dir.exists()


def test_write_event_proposal_file_success(tmp_path):
    vault_root = tmp_path / "vault"
    event = ExtractedEvent(local_id="ev1", text="An event", epistemic_status="direct", starts_at=None, ends_at=None)
    proposal_id = storage.write_event_proposal_file(vault_root, "PERSONAL", event, "src-abc", "TestProvider")
    path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    assert path.exists()


def test_validate_frontmatter_missing_field_raises():
    with pytest.raises(ValidationError):
        storage._validate_frontmatter({"a": 1}, ["a", "b"])


def test_validate_frontmatter_all_present_ok():
    storage._validate_frontmatter({"a": 1, "b": 2}, ["a", "b"])


def test_atomic_write_creates_file_no_leftover_tmp(tmp_path):
    path = tmp_path / "domain" / "sources" / "src-x" / "src-x.md"
    storage._write_atomic_file(path, "content")
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "content"
    leftover_tmp = list(path.parent.glob("*.tmp"))
    assert leftover_tmp == []


def test_atomic_write_cleans_up_tmp_on_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "domain" / "sources" / "src-x" / "src-x.md"

    def failing_replace(src, dst):
        raise OSError("simulated os.replace failure")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError):
        storage._write_atomic_file(path, "content")

    assert not path.exists()
    leftover_tmp = list(path.parent.glob("*.tmp"))
    assert leftover_tmp == [], "orphaned .tmp file left behind after os.replace failure"


def test_no_rollback_target_file_untouched_on_replace_failure(tmp_path, monkeypatch):
    path = tmp_path / "domain" / "sources" / "src-x" / "src-x.md"
    path.parent.mkdir(parents=True)
    path.write_text("original", encoding="utf-8")

    def failing_replace(src, dst):
        raise OSError("simulated os.replace failure")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError):
        storage._write_atomic_file(path, "new content")

    assert path.read_text(encoding="utf-8") == "original"


# TASK-005a: ADI-012 adoption by entity/event/relationship - proposal frontmatter
# carries proposed_path_segments (AC13), and the two new existing-folder scans
# (AC14).

def test_write_entity_proposal_file_includes_proposed_path_segments(tmp_path):
    vault_root = tmp_path / "vault"
    entity = ExtractedEntity(
        local_id="e1", entity_type="person", text="Ada", epistemic_status="direct",
        proposed_path_segments=["personnages", "historiques"],
    )
    proposal_id = storage.write_entity_proposal_file(vault_root, "PERSONAL", entity, "src-abc", "TestProvider")
    path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    fm, _ = read_frontmatter(path)
    assert fm["proposed_path_segments"] == ["personnages", "historiques"]


def test_write_event_proposal_file_default_proposed_path_segments_is_empty_list(tmp_path):
    """Field is always written, defaulting to [] - never omitted."""
    vault_root = tmp_path / "vault"
    event = ExtractedEvent(local_id="ev1", text="An event", epistemic_status="direct")
    proposal_id = storage.write_event_proposal_file(vault_root, "PERSONAL", event, "src-abc", "TestProvider")
    path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    fm, _ = read_frontmatter(path)
    assert fm["proposed_path_segments"] == []


def test_write_relationship_proposal_file_includes_proposed_path_segments(tmp_path):
    vault_root = tmp_path / "vault"
    relationship = ExtractedRelationship(
        text="Ada knows Charles", epistemic_status="direct", relationship_type="knows",
        endpoints=["e1", "e2"], proposed_path_segments=["famille"],
    )
    proposal_id = storage.write_relationship_proposal_file(
        vault_root, "PERSONAL", relationship, ["entity-a", "entity-b"], "src-abc", "TestProvider"
    )
    path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    fm, _ = read_frontmatter(path)
    assert fm["proposed_path_segments"] == ["famille"]


def test_required_proposal_fields_does_not_require_proposed_path_segments():
    """AC13: a hand-written or pre-existing proposal lacking the key must still
    validate (and, per review/pipeline.py's accept_proposal, still accept)."""
    frontmatter_without_key = {
        "id": "prop-1", "type": "proposal", "item_type": "proposal", "domain": "PERSONAL",
        "created_at": "2026-01-01T00:00:00", "proposal_status": "PROPOSED",
        "provenance": {"source_id": "src-1", "extraction_provider": "TestProvider"},
        "proposed_item_type": "entity", "epistemic_status": "direct",
        "valid_from": "2026-01-01T00:00:00", "valid_until": None,
    }
    storage._validate_frontmatter(frontmatter_without_key, storage.REQUIRED_PROPOSAL_FIELDS)


def test_scan_existing_item_folders_empty_when_missing(tmp_path):
    assert storage.scan_existing_item_folders(tmp_path, "PERSONAL", "entity") == []


def test_scan_existing_item_folders_returns_full_paths_scoped_by_type(tmp_path):
    entities_dir = tmp_path / "PERSONAL" / "entities"
    (entities_dir / "personnages" / "historiques" / "entity-1").mkdir(parents=True)
    (entities_dir / "lieux" / "entity-2").mkdir(parents=True)
    events_dir = tmp_path / "PERSONAL" / "events"
    (events_dir / "guerre" / "event-1").mkdir(parents=True)

    entity_paths = storage.scan_existing_item_folders(tmp_path, "PERSONAL", "entity")
    assert sorted(entity_paths) == ["lieux", "personnages", "personnages/historiques"]
    assert storage.scan_existing_item_folders(tmp_path, "PERSONAL", "event") == ["guerre"]
    assert storage.scan_existing_item_folders(tmp_path, "PERSONAL", "relationship") == []


def test_scan_existing_item_folders_excludes_own_id_prefix_as_leaf(tmp_path):
    entities_dir = tmp_path / "PERSONAL" / "entities"
    (entities_dir / "entity-standalone").mkdir(parents=True)

    assert storage.scan_existing_item_folders(tmp_path, "PERSONAL", "entity") == []


def test_scan_proposed_path_segments_empty_when_missing(tmp_path):
    assert storage.scan_proposed_path_segments(tmp_path, "PERSONAL", "entity") == []


def test_scan_proposed_path_segments_filters_by_status_and_item_type(tmp_path):
    proposals_dir = tmp_path / "PERSONAL" / "proposals"

    def _write(proposal_id, proposal_status, proposed_item_type, proposed_path_segments):
        path = proposals_dir / proposal_id / f"{proposal_id}.md"
        path.parent.mkdir(parents=True)
        frontmatter = {
            "proposal_status": proposal_status,
            "proposed_item_type": proposed_item_type,
            "proposed_path_segments": proposed_path_segments,
        }
        path.write_text(f"---\n{yaml.dump(frontmatter)}---\n\nbody", encoding="utf-8")

    _write("prop-1", "PROPOSED", "entity", ["personnages"])
    _write("prop-2", "EDITED", "entity", ["lieux"])
    _write("prop-3", "ACCEPTED", "entity", ["should-not-appear"])
    _write("prop-4", "PROPOSED", "event", ["guerre"])  # different type - excluded
    _write("prop-5", "PROPOSED", "entity", [])  # empty segments - excluded

    assert storage.scan_proposed_path_segments(tmp_path, "PERSONAL", "entity") == ["lieux", "personnages"]


def test_scan_proposed_path_segments_malformed_proposal_file_does_not_raise(tmp_path):
    proposals_dir = tmp_path / "PERSONAL" / "proposals" / "prop-bad"
    proposals_dir.mkdir(parents=True)
    (proposals_dir / "prop-bad.md").write_text("not a valid frontmatter file at all", encoding="utf-8")

    assert storage.scan_proposed_path_segments(tmp_path, "PERSONAL", "entity") == []


def test_scan_proposed_path_segments_ignores_invalid_yaml_proposal_file(tmp_path):
    """A file whose frontmatter block exists but is invalid YAML must not break
    the scan for other, well-formed proposals."""
    proposals_dir = tmp_path / "PERSONAL" / "proposals"
    bad_dir = proposals_dir / "prop-bad-yaml"
    bad_dir.mkdir(parents=True)
    (bad_dir / "prop-bad-yaml.md").write_text("---\nkey: [unclosed\n---\n\nBody.", encoding="utf-8")
    good_dir = proposals_dir / "prop-good"
    good_dir.mkdir(parents=True)
    good_dir_frontmatter = {
        "proposal_status": "PROPOSED", "proposed_item_type": "entity",
        "proposed_path_segments": ["personnages"],
    }
    (good_dir / "prop-good.md").write_text(
        f"---\n{yaml.dump(good_dir_frontmatter)}---\n\nBody.", encoding="utf-8"
    )

    assert storage.scan_proposed_path_segments(tmp_path, "PERSONAL", "entity") == ["personnages"]
