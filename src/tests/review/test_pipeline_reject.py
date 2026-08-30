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
