"""
Unit tests for pipeline.reject_proposal (acceptance criteria 2, 3, 4).
"""
import pytest

from src.app.review import pipeline
from src.app.review.errors import DomainMismatchError, InvalidProposalStatusError
from src.app.review.frontmatter import parse_frontmatter


def test_reject_proposal_sets_status_reviewed_by_reviewed_at(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    result = pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1", reason="not relevant")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "REJECTED"
    assert proposal_frontmatter["reviewed_by"] == "reviewer-1"
    assert proposal_frontmatter["reviewed_at"] == result.reviewed_at


def test_reject_proposal_resulting_item_id_stays_null(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["resulting_item_id"] is None


def test_reject_proposal_no_assertion_file_written(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert not (tmp_path / "PERSONAL" / "assertions").exists()


def test_reject_proposal_preserves_other_fields_including_body(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", body="Original body text.")
    original_frontmatter, original_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, proposal_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_body == original_body == "Original body text."
    assert proposal_frontmatter["id"] == original_frontmatter["id"]
    assert proposal_frontmatter["epistemic_status"] == original_frontmatter["epistemic_status"]
    assert proposal_frontmatter["provenance"] == original_frontmatter["provenance"]


def test_reject_proposal_with_reason_stores_rejection_reason(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1", reason="duplicate")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["rejection_reason"] == "duplicate"


def test_reject_proposal_without_reason_rejection_reason_is_null(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["rejection_reason"] is None


def test_reject_proposal_no_history_subfolder_created(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert not (tmp_path / "PERSONAL" / "proposals" / proposal_id / "history").exists()


def test_reject_already_rejected_proposal_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")
    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_reject_then_accept_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")
    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_reject_accepted_proposal_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_reject_proposal_wrong_domain_raises_domain_mismatch(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", internal_domain="FICTION")

    with pytest.raises(DomainMismatchError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")


def test_reject_proposal_succeeds_on_edited_status(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", status="EDITED")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "REJECTED"
    assert proposal_frontmatter["resulting_item_id"] is None


def test_reject_proposal_after_edit_preserves_edited_content_unchanged(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", body="Original body.")
    pipeline.edit_proposal(tmp_path, "PERSONAL", proposal_id, "editor-1", body="Edited body.")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, proposal_body = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_body == "Edited body."
    assert proposal_frontmatter["proposal_status"] == "REJECTED"


def test_reject_already_edited_then_rejected_proposal_raises_on_second_reject(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", status="EDITED")
    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


# TASK-005: reject for entity/event/relationship (identical, type-agnostic behavior)

def test_reject_entity_proposal_sets_status_and_writes_no_canonical_file(
    tmp_path, make_entity_proposal_file
):
    proposal_id, proposal_file = make_entity_proposal_file(domain="PERSONAL")

    result = pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1", reason="not relevant")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "REJECTED"
    assert proposal_frontmatter["reviewed_by"] == "reviewer-1"
    assert proposal_frontmatter["reviewed_at"] == result.reviewed_at
    assert proposal_frontmatter["resulting_item_id"] is None
    assert not (tmp_path / "PERSONAL" / "entities").exists()


def test_reject_event_proposal_sets_status_and_writes_no_canonical_file(
    tmp_path, make_event_proposal_file
):
    proposal_id, proposal_file = make_event_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "REJECTED"
    assert not (tmp_path / "PERSONAL" / "events").exists()


def test_reject_relationship_proposal_sets_status_and_writes_no_canonical_file(
    tmp_path, make_relationship_proposal_file
):
    proposal_id, proposal_file = make_relationship_proposal_file(domain="PERSONAL")

    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "REJECTED"
    assert not (tmp_path / "PERSONAL" / "relationships").exists()


@pytest.mark.parametrize("proposed_item_type", ["entity", "event", "relationship"])
def test_double_transition_after_reject_raises_for_new_types(
    tmp_path, make_proposal_file, proposed_item_type
):
    extra = {}
    if proposed_item_type == "entity":
        extra["entity_type"] = "person"
    elif proposed_item_type == "event":
        extra["starts_at"] = "2026-01-01T00:00:00"
        extra["ends_at"] = None
    elif proposed_item_type == "relationship":
        extra["relationship_type"] = "knows"
        extra["endpoints"] = ["a", "b"]

    proposal_id, _ = make_proposal_file(domain="PERSONAL", proposed_item_type=proposed_item_type, **extra)
    pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")
