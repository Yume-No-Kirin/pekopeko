"""
Unit tests for pipeline.accept_proposal (acceptance criteria 1, 3, 4, 5).
"""
import pytest

from src.app.review import pipeline, storage
from src.app.review.errors import (
    DomainMismatchError,
    InvalidProposalStatusError,
    ProposalNotFoundError,
    UnsupportedProposalTypeError,
    ValidationError,
)
from src.app.review.frontmatter import parse_frontmatter


def test_accept_proposal_writes_assertion_with_all_required_frontmatter(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", epistemic_status="inferred", body="Body text.")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path.exists()
    assertion_frontmatter, assertion_body = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))

    assert assertion_frontmatter["id"] == result.assertion_id
    assert assertion_frontmatter["type"] == "assertion"
    assert assertion_frontmatter["domain"] == "PERSONAL"
    assert assertion_frontmatter["epistemic_status"] == "inferred"
    assert assertion_frontmatter["lifecycle_status"] == "ACTIVE"
    assert assertion_body == "Body text."


def test_accept_proposal_carries_over_valid_from_valid_until(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(
        domain="PERSONAL", valid_from="2020-01-01T00:00:00", valid_until="2020-12-31T00:00:00"
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assertion_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert assertion_frontmatter["valid_from"] == "2020-01-01T00:00:00"
    assert assertion_frontmatter["valid_until"] == "2020-12-31T00:00:00"


def test_accept_proposal_provenance_fields(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", source_id="src-known", extraction_provider="OllamaProvider")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assertion_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    provenance = assertion_frontmatter["provenance"]
    assert provenance["source_id"] == "src-known"
    assert provenance["extraction_provider"] == "OllamaProvider"
    assert provenance["proposal_id"] == proposal_id
    assert provenance["reviewed_by"] == "reviewer-1"
    assert provenance["reviewed_at"] == result.reviewed_at


def test_accept_proposal_created_at_is_acceptance_time_not_proposal_created_at(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", created_at="2020-01-01T00:00:00")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assertion_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert assertion_frontmatter["created_at"] != "2020-01-01T00:00:00"


def test_accept_proposal_updates_proposal_fields(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["proposal_status"] == "ACCEPTED"
    assert proposal_frontmatter["reviewed_by"] == "reviewer-1"
    assert proposal_frontmatter["reviewed_at"] == result.reviewed_at
    assert proposal_frontmatter["resulting_item_id"] == result.assertion_id


def test_accept_proposal_no_history_subfolder_created(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert not (tmp_path / "PERSONAL" / "proposals" / proposal_id / "history").exists()


def test_accept_proposal_preserves_unrelated_proposal_fields(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(
        domain="PERSONAL",
        epistemic_status="uncertain",
        created_at="2020-01-01T00:00:00",
        valid_from="2020-01-01T00:00:00",
        valid_until="2020-06-01T00:00:00",
    )

    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    proposal_frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
    assert proposal_frontmatter["id"] == proposal_id
    assert proposal_frontmatter["type"] == "proposal"
    assert proposal_frontmatter["domain"] == "PERSONAL"
    assert proposal_frontmatter["proposed_item_type"] == "assertion"
    assert proposal_frontmatter["epistemic_status"] == "uncertain"
    assert proposal_frontmatter["created_at"] == "2020-01-01T00:00:00"
    assert proposal_frontmatter["valid_from"] == "2020-01-01T00:00:00"
    assert proposal_frontmatter["valid_until"] == "2020-06-01T00:00:00"


def test_accept_already_accepted_proposal_raises_and_leaves_files_unchanged(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")
    content_after_first_accept = proposal_file.read_text(encoding="utf-8")
    assertions_before = sorted(p.name for p in (tmp_path / "PERSONAL" / "assertions").iterdir())

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")

    assert proposal_file.read_text(encoding="utf-8") == content_after_first_accept
    assertions_after = sorted(p.name for p in (tmp_path / "PERSONAL" / "assertions").iterdir())
    assert assertions_after == assertions_before


def test_accept_then_reject_raises_invalid_status(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_accept_proposal_wrong_domain_raises_domain_mismatch(tmp_path, make_proposal_file):
    # File is physically stored under PERSONAL/, but its own frontmatter
    # says domain: FICTION - the mismatch DomainMismatchError guards against.
    proposal_id, _ = make_proposal_file(domain="PERSONAL", internal_domain="FICTION")

    with pytest.raises(DomainMismatchError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")


def test_accept_nonexistent_proposal_raises_proposal_not_found(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", "prop-missing", "reviewer-1")


def test_accept_proposal_missing_reviewer_id_raises_validation_error(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    with pytest.raises(ValidationError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "")


def test_accept_proposal_unsupported_proposed_item_type_raises(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", proposed_item_type="bogus")

    with pytest.raises(UnsupportedProposalTypeError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")


def test_accept_proposal_assertion_write_failure_leaves_proposal_untouched(tmp_path, monkeypatch, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(storage, "write_assertion_file", boom)

    with pytest.raises(OSError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert proposal_file.read_text(encoding="utf-8") == original_content


def test_accept_proposal_assertion_write_failure_no_orphan_assertion_file(tmp_path, monkeypatch, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    def boom(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(storage, "write_assertion_file", boom)

    with pytest.raises(OSError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assertions_dir = tmp_path / "PERSONAL" / "assertions"
    assert not assertions_dir.exists() or list(assertions_dir.iterdir()) == []


def test_accept_proposal_succeeds_on_edited_status(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", status="EDITED")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path.exists()
    assertion_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert assertion_frontmatter["lifecycle_status"] == "ACTIVE"


def test_accept_proposal_after_edit_writes_assertion_from_edited_body_and_fields(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(
        domain="PERSONAL", body="Original body.", epistemic_status="direct"
    )
    pipeline.edit_proposal(
        tmp_path, "PERSONAL", proposal_id, "editor-1",
        body="Edited body.", field_updates={"epistemic_status": "uncertain"},
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assertion_frontmatter, assertion_body = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert assertion_body == "Edited body."
    assert assertion_frontmatter["epistemic_status"] == "uncertain"


def test_accept_already_edited_then_accepted_proposal_raises_on_second_accept(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", status="EDITED")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


# TASK-014: folder-path organization (assertion-only)

def test_accept_proposal_writes_segmented_path_when_proposed_path_segments_present(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", proposed_path_segments=["x", "y"])

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    expected = tmp_path / "PERSONAL" / "assertions" / "x" / "y" / result.assertion_id / f"{result.assertion_id}.md"
    assert result.assertion_path == expected
    assert result.assertion_path.exists()


def test_accept_proposal_writes_plain_path_when_proposed_path_segments_absent(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    expected = tmp_path / "PERSONAL" / "assertions" / result.assertion_id / f"{result.assertion_id}.md"
    assert result.assertion_path == expected


def test_accept_proposal_rejects_invalid_path_segments_before_any_write(tmp_path, make_proposal_file):
    proposal_id, proposal_file = make_proposal_file(domain="PERSONAL", proposed_path_segments=["a/b"])
    original_content = proposal_file.read_text(encoding="utf-8")

    with pytest.raises(ValidationError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert proposal_file.read_text(encoding="utf-8") == original_content
    assertions_dir = tmp_path / "PERSONAL" / "assertions"
    assert not assertions_dir.exists() or list(assertions_dir.iterdir()) == []
