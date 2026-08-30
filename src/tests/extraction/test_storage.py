"""
storage.py unit tests: atomic writes (AC8), frontmatter/domain validation.
"""
import os
from pathlib import Path

import pytest

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
