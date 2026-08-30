"""
Unit tests for review/storage.py: atomic writes, path helpers, validation.
"""
import os

import pytest

from src.app.review import storage
from src.app.review.errors import (
    InvalidDomainError,
    ProposalNotFoundError,
    SourceNotFoundError,
    ValidationError,
)


def test_write_atomic_file_creates_parent_dirs(tmp_path):
    target = tmp_path / "a" / "b" / "c.md"

    storage._write_atomic_file(target, "content")

    assert target.read_text(encoding="utf-8") == "content"


def test_write_atomic_file_failure_leaves_no_partial_file(tmp_path, monkeypatch):
    target = tmp_path / "PERSONAL" / "assertions" / "assert-x" / "assert-x.md"

    def failing_replace(src, dst):
        raise OSError("simulated failure during rename")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError):
        storage._write_atomic_file(target, "---\nfoo: bar\n---\n\nbody")

    assert not target.exists()
    assert list(target.parent.glob("*.tmp")) == []


def test_generate_assertion_id_format_and_uniqueness():
    id1 = storage._generate_assertion_id()
    id2 = storage._generate_assertion_id()

    assert id1.startswith("assert-")
    assert id1 != id2


def test_list_proposal_ids_empty_when_no_proposals_dir(tmp_path):
    assert storage.list_proposal_ids(tmp_path, "PERSONAL") == []


def test_read_proposal_file_raises_proposal_not_found(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        storage.read_proposal_file(tmp_path, "PERSONAL", "prop-missing")


def test_read_source_file_raises_source_not_found(tmp_path):
    with pytest.raises(SourceNotFoundError):
        storage.read_source_file(tmp_path, "PERSONAL", "src-missing")


def test_validate_domain_rejects_invalid_domain():
    with pytest.raises(InvalidDomainError):
        storage._validate_domain("NOT_A_DOMAIN")


def test_validate_domain_accepts_all_valid_domains():
    for domain in storage.VALID_DOMAINS:
        storage._validate_domain(domain)


def test_write_assertion_file_raises_validation_error_before_write_on_missing_fields(tmp_path):
    incomplete_frontmatter = {"id": "assert-1", "type": "assertion"}

    with pytest.raises(ValidationError):
        storage.write_assertion_file(tmp_path, "PERSONAL", incomplete_frontmatter, "body")

    assert not (tmp_path / "PERSONAL" / "assertions").exists()
