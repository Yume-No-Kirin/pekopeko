"""
Unit tests for pipeline.edit_proposal (acceptance criteria 1-7, 11, 12).
"""
import os

import pytest

from src.app.review import pipeline, storage
from src.app.review.errors import (
    DomainMismatchError,
    InvalidProposalStatusError,
    UneditableFieldError,
    ValidationError,
)
from src.app.review.frontmatter import parse_frontmatter


def test_edit_proposal_body_archives_pre_edit_content_and_updates_live_file(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", body="Original body.")
    original_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))

    result = pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    history_files = list(history_dir.glob("*--v1.md"))
    assert len(history_files) == 1
    snapshot_frontmatter, snapshot_body = parse_frontmatter(history_files[0].read_text(encoding="utf-8"))
    assert snapshot_frontmatter["lifecycle_status"] == "SUPERSEDED"
    assert snapshot_frontmatter["superseded_by"] == "v2"
    assert snapshot_body == "Original body."

    live_frontmatter, live_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_body == "New body."
    assert live_frontmatter["proposal_status"] == "EDITED"
    assert live_frontmatter["edited_by"] == "editor-1"
    assert live_frontmatter["edited_at"] == result.edited_at
    assert live_frontmatter["id"] == original_frontmatter["id"]
    assert live_frontmatter["domain"] == original_frontmatter["domain"]
    assert live_frontmatter["provenance"] == original_frontmatter["provenance"]


def test_edit_proposal_field_update_assertion(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", epistemic_status="direct", body="Body.")

    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", field_updates={"epistemic_status": "uncertain"})

    live_frontmatter, live_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_frontmatter["epistemic_status"] == "uncertain"
    assert live_body == "Body."


def test_edit_proposal_field_update_entity(tmp_path, make_entity_proposal_file):
    proposal_id, proposal_file = make_entity_proposal_file(domain="PERSONAL", entity_type="person")

    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", field_updates={"entity_type": "organization"})

    live_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_frontmatter["entity_type"] == "organization"


def test_edit_proposal_field_update_event(tmp_path, make_event_proposal_file):
    proposal_id, proposal_file = make_event_proposal_file(
        domain="PERSONAL", starts_at="2026-01-01T00:00:00", ends_at="2026-01-02T00:00:00"
    )

    pipeline.edit_proposal(
        tmp_path, "PERSONAL", proposal_id, "editor-1",
        field_updates={"starts_at": "2026-02-01T00:00:00", "ends_at": "2026-02-02T00:00:00"},
    )

    live_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_frontmatter["starts_at"] == "2026-02-01T00:00:00"
    assert live_frontmatter["ends_at"] == "2026-02-02T00:00:00"


def test_edit_proposal_field_update_relationship(tmp_path, make_relationship_proposal_file):
    proposal_id, proposal_file = make_relationship_proposal_file(domain="PERSONAL", relationship_type="knows")

    pipeline.edit_proposal(
        tmp_path, "PERSONAL", proposal_id, "editor-1",
        field_updates={"relationship_type": "employs", "endpoints": {"from": "entity-x", "to": "entity-y"}},
    )

    live_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_frontmatter["relationship_type"] == "employs"
    assert live_frontmatter["endpoints"] == {"from": "entity-x", "to": "entity-y"}


def test_edit_proposal_uneditable_field_raises_before_any_write(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(UneditableFieldError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", field_updates={"id": "new-id"})

    assert proposal_file.read_text(encoding="utf-8") == original_content
    assert not storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id).exists()


def test_edit_proposal_uneditable_cross_type_field_raises(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(UneditableFieldError):
        pipeline.edit_proposal(
            tmp_path, "PERSONAL", proposal_id, "editor-1",
            field_updates={"endpoints": {"from": "a", "to": "b"}},
        )

    assert proposal_file.read_text(encoding="utf-8") == original_content
    assert not storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id).exists()


def test_edit_proposal_system_managed_field_raises(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(UneditableFieldError):
        pipeline.edit_proposal(
            tmp_path, "PERSONAL", proposal_id, "editor-1",
            field_updates={"provenance": {}},
        )

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_twice_creates_independent_snapshots(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", body="v0 body.")

    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="v1 body.")
    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    v1_files_after_first_edit = list(history_dir.glob("*--v1.md"))
    assert len(v1_files_after_first_edit) == 1
    v1_content_after_first_edit = v1_files_after_first_edit[0].read_text(encoding="utf-8")

    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="v2 body.")

    v1_files_after_second_edit = list(history_dir.glob("*--v1.md"))
    v2_files = list(history_dir.glob("*--v2.md"))
    assert len(v1_files_after_second_edit) == 1
    assert v1_files_after_second_edit[0].read_text(encoding="utf-8") == v1_content_after_first_edit
    assert len(v2_files) == 1
    v2_frontmatter, v2_body = parse_frontmatter(v2_files[0].read_text(encoding="utf-8"))
    assert v2_frontmatter["superseded_by"] == "v3"
    assert v2_body == "v1 body."

    live_frontmatter, live_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_body == "v2 body."
    assert live_frontmatter["proposal_status"] == "EDITED"


def test_edit_proposal_succeeds_for_assertion(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", proposed_item_type="assertion")

    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="Edited.")


def test_edit_proposal_succeeds_for_entity(tmp_path, make_entity_proposal_file):
    proposal_id, _ = make_entity_proposal_file(domain="PERSONAL")

    result = pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="Edited.")

    assert result.proposal_id == proposal_id


def test_edit_proposal_succeeds_for_event(tmp_path, make_event_proposal_file):
    proposal_id, _ = make_event_proposal_file(domain="PERSONAL")

    result = pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="Edited.")

    assert result.proposal_id == proposal_id


def test_edit_proposal_succeeds_for_relationship(tmp_path, make_relationship_proposal_file):
    proposal_id, _ = make_relationship_proposal_file(domain="PERSONAL")

    result = pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="Edited.")

    assert result.proposal_id == proposal_id


def test_edit_proposal_no_body_and_no_field_updates_raises_validation_error(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(ValidationError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1")

    assert proposal_file.read_text(encoding="utf-8") == original_content
    assert not storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id).exists()


def test_edit_proposal_empty_field_updates_and_no_body_raises_validation_error(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(ValidationError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", field_updates={})

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_on_accepted_proposal_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", status="ACCEPTED")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_on_rejected_proposal_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", status="REJECTED")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_wrong_domain_raises_domain_mismatch(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", internal_domain="FICTION")

    with pytest.raises(DomainMismatchError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")


def test_edit_proposal_missing_reviewer_id_raises_validation_error(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    with pytest.raises(ValidationError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "", body="New body.")


def test_edit_proposal_archive_write_failure_leaves_live_file_untouched(tmp_path, monkeypatch, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(storage, "archive_proposal_version", boom)

    with pytest.raises(OSError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_archive_write_failure_no_orphaned_history_file(tmp_path, monkeypatch, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    def boom(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(storage, "archive_proposal_version", boom)

    with pytest.raises(OSError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    assert not history_dir.exists() or list(history_dir.iterdir()) == []


def test_edit_proposal_archive_write_is_atomic_no_partial_file_on_replace_failure(tmp_path, monkeypatch, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    def failing_replace(src, dst):
        raise OSError("simulated failure during rename")

    monkeypatch.setattr(os, "replace", failing_replace)

    with pytest.raises(OSError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    # The archive write (first os.replace call) failed atomically: no partial
    # snapshot and no orphaned .tmp file, live file untouched since it is never
    # reached when the archive step itself fails.
    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    assert not history_dir.exists() or list(history_dir.glob("*.tmp")) == []
    assert not history_dir.exists() or list(history_dir.glob("*.md")) == []
    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_edit_proposal_live_overwrite_failure_leaves_archived_snapshot_and_pre_edit_live_content(
    tmp_path, monkeypatch, make_proposal_file
):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", body="Original body.")
    original_content = proposal_file.read_text(encoding="utf-8")

    real_replace = os.replace
    call_count = {"n": 0}

    def flaky_replace(src, dst):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise OSError("simulated failure during live-file rename")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky_replace)

    with pytest.raises(OSError):
        pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="New body.")

    # Archive write (1st os.replace call) succeeded and remains, as an inert
    # extra file; live file's 2nd os.replace failed, so it is left untouched.
    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    assert len(list(history_dir.glob("*--v1.md"))) == 1
    assert list(proposal_file.parent.glob("*.tmp")) == []
    assert proposal_file.read_text(encoding="utf-8") == original_content


# TASK-014: folder-path organization (assertion-only)

def test_edit_proposal_field_update_assertion_proposed_path_segments(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    pipeline.edit_proposal(
        tmp_path, "PERSONAL", proposal_id, "editor-1",
        field_updates={"proposed_path_segments": ["a", "b"]},
    )

    live_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert live_frontmatter["proposed_path_segments"] == ["a", "b"]
    history_dir = storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id)
    assert len(list(history_dir.glob("*--v1.md"))) == 1


def test_edit_proposal_proposed_path_segments_uneditable_for_non_assertion(tmp_path, make_entity_proposal_file):
    proposal_id, proposal_file = make_entity_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(UneditableFieldError):
        pipeline.edit_proposal(
            tmp_path, "PERSONAL", proposal_id, "editor-1",
            field_updates={"proposed_path_segments": ["a"]},
        )

    assert proposal_file.read_text(encoding="utf-8") == original_content
    assert not storage.proposal_history_dir(tmp_path, "PERSONAL", proposal_id).exists()
