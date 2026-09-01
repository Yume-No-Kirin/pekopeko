"""
Unit tests for review/storage.py: atomic writes, path helpers, validation.
"""
import os
import time

import pytest

from src.app.review import storage
from src.app.review.errors import (
    InvalidDomainError,
    ProposalNotFoundError,
    SourceNotFoundError,
    UneditableFieldError,
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


def test_next_history_version_returns_1_when_dir_missing(tmp_path):
    assert storage._next_history_version(tmp_path / "nonexistent" / "history") == 1


def test_next_history_version_returns_1_when_dir_empty(tmp_path):
    history_dir = tmp_path / "history"
    history_dir.mkdir()

    assert storage._next_history_version(history_dir) == 1


def test_next_history_version_parses_max_existing_version_plus_one(tmp_path):
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    (history_dir / "20260101T000000000000--v1.md").write_text("x", encoding="utf-8")
    (history_dir / "20260101T000001000000--v2.md").write_text("x", encoding="utf-8")

    assert storage._next_history_version(history_dir) == 3


def test_next_history_version_ignores_malformed_filenames(tmp_path):
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    (history_dir / "20260101T000000000000--v1.md").write_text("x", encoding="utf-8")
    (history_dir / "not-a-history-file.tmp").write_text("x", encoding="utf-8")
    (history_dir / ".DS_Store").write_text("x", encoding="utf-8")

    assert storage._next_history_version(history_dir) == 2


def test_archive_proposal_version_writes_snapshot_with_lifecycle_and_superseded_by(tmp_path):
    frontmatter = {"id": "prop-1", "domain": "PERSONAL", "proposal_status": "PROPOSED"}

    path, version = storage.archive_proposal_version(tmp_path, "PERSONAL", "prop-1", frontmatter, "body text")

    assert version == 1
    assert path.exists()
    assert path.parent == storage.proposal_history_dir(tmp_path, "PERSONAL", "prop-1")
    from src.app.review.frontmatter import parse_frontmatter
    snapshot_frontmatter, snapshot_body = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert snapshot_frontmatter["lifecycle_status"] == "SUPERSEDED"
    assert snapshot_frontmatter["superseded_by"] == "v2"
    assert snapshot_body == "body text"
    # Caller's dict must not be mutated.
    assert "lifecycle_status" not in frontmatter


def test_archive_proposal_version_second_call_gets_v2_and_leaves_v1_untouched(tmp_path):
    frontmatter = {"id": "prop-1", "domain": "PERSONAL", "proposal_status": "PROPOSED"}

    path1, version1 = storage.archive_proposal_version(tmp_path, "PERSONAL", "prop-1", frontmatter, "v1 body")
    content_after_first = path1.read_text(encoding="utf-8")
    path2, version2 = storage.archive_proposal_version(tmp_path, "PERSONAL", "prop-1", frontmatter, "v2 body")

    assert version1 == 1
    assert version2 == 2
    assert path1.read_text(encoding="utf-8") == content_after_first
    assert path1 != path2


def test_validate_editable_fields_allows_common_fields_for_all_types():
    for item_type in ("assertion", "entity", "event", "relationship"):
        storage._validate_editable_fields(item_type, {"epistemic_status": "uncertain"})


def test_validate_editable_fields_raises_for_disallowed_field():
    with pytest.raises(UneditableFieldError):
        storage._validate_editable_fields("assertion", {"id": "new-id"})


def test_validate_editable_fields_raises_for_cross_type_field():
    with pytest.raises(UneditableFieldError):
        storage._validate_editable_fields("assertion", {"endpoints": {"from": "a", "to": "b"}})


def test_validate_editable_fields_raises_for_unknown_proposed_item_type():
    with pytest.raises(ValidationError):
        storage._validate_editable_fields("not-a-real-type", {"epistemic_status": "uncertain"})


def test_proposal_edit_lock_serializes_concurrent_archive_calls(tmp_path):
    """Two overlapping edit_proposal calls must not compute the same next
    history version (the race this lock exists to close)."""
    import threading

    frontmatter = {"id": "prop-1", "domain": "PERSONAL", "proposal_status": "PROPOSED"}
    barrier = threading.Barrier(2)
    versions = []

    def racer(body):
        barrier.wait(timeout=5)  # both threads race to acquire the lock together
        with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
            _, version = storage.archive_proposal_version(tmp_path, "PERSONAL", "prop-1", frontmatter, body)
            versions.append(version)

    t1 = threading.Thread(target=racer, args=("body-a",))
    t2 = threading.Thread(target=racer, args=("body-b",))
    t1.start()
    t2.start()
    t1.join(timeout=5)
    t2.join(timeout=5)

    assert sorted(versions) == [1, 2]


def test_proposal_edit_lock_released_on_exception(tmp_path):
    with pytest.raises(ValueError):
        with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
            raise ValueError("boom")

    lock_path = storage.proposal_path(tmp_path, "PERSONAL", "prop-1").parent / ".edit.lock"
    assert not lock_path.exists()

    # Lock is immediately reusable afterwards.
    with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
        pass


def test_proposal_edit_lock_steals_stale_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_EDIT_LOCK_STALE_SECONDS", 0)
    lock_path = storage.proposal_path(tmp_path, "PERSONAL", "prop-1").parent / ".edit.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("held by a crashed process", encoding="utf-8")
    old_time = time.time() - 100
    os.utime(lock_path, (old_time, old_time))

    # Succeeds without waiting for the full timeout, by stealing the stale lock.
    with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
        pass


def test_proposal_edit_lock_times_out_when_already_held(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_EDIT_LOCK_TIMEOUT_SECONDS", 0.1)
    monkeypatch.setattr(storage, "_EDIT_LOCK_STALE_SECONDS", 999)
    monkeypatch.setattr(storage, "_EDIT_LOCK_POLL_SECONDS", 0.01)
    lock_path = storage.proposal_path(tmp_path, "PERSONAL", "prop-1").parent / ".edit.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("held", encoding="utf-8")

    with pytest.raises(TimeoutError):
        with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
            pass


def test_proposal_edit_lock_retries_on_getmtime_race(tmp_path, monkeypatch):
    """If the lock file vanishes between the FileExistsError and the staleness
    check (another holder released it concurrently), retry instead of crashing."""
    lock_path = storage.proposal_path(tmp_path, "PERSONAL", "prop-1").parent / ".edit.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    real_open = os.open
    calls = {"n": 0}

    def flaky_open(path, flags, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise FileExistsError()
        return real_open(path, flags, *args, **kwargs)

    def flaky_getmtime(path):
        raise OSError("simulated race: lock file vanished")

    monkeypatch.setattr(storage.os, "open", flaky_open)
    monkeypatch.setattr(storage.os.path, "getmtime", flaky_getmtime)

    with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
        pass

    assert calls["n"] == 2


def test_proposal_edit_lock_release_swallows_remove_error(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.os, "remove", lambda path: (_ for _ in ()).throw(OSError("boom")))

    with storage.proposal_edit_lock(tmp_path, "PERSONAL", "prop-1"):
        pass
