"""
UC-011 (Review Queue, V1 individual-review slice - the best-covered UC in
the repo) and UC-014 (Source-Based QA, provenance/source-resolution slice
only). See specs/tests/test-plan.md, TC-UC011-01..05, TC-UC014-01.

Covers: status-filtered listing, get_proposal's resolved source content,
edit + history versioning, reject with reason, and the invalid-transition
guard - TASK-002 AC1/2/4/6/7 and TASK-006 AC1/8/9/10.
"""
from _acceptance_helpers import FixedIngestionProvider, read_frontmatter

from src.app.ingestion.pipeline import ingest_source
from src.app.ingestion.providers.base import ExtractedAssertion
from src.app.review.errors import InvalidProposalStatusError
from src.app.review.pipeline import accept_proposal, edit_proposal, get_proposal, list_proposals, reject_proposal


def _ingest_two_assertions(vault_root, state_dir, tmp_path):
    source_a = tmp_path / "a.md"
    source_a.write_text("Source A content.", encoding="utf-8")
    source_b = tmp_path / "b.md"
    source_b.write_text("Source B content.", encoding="utf-8")

    result_a = ingest_source(
        vault_root, "PERSONAL", source_a,
        FixedIngestionProvider(assertions=[ExtractedAssertion(text="Assertion A.", epistemic_status="direct")]),
        state_dir=state_dir,
    )
    result_b = ingest_source(
        vault_root, "PERSONAL", source_b,
        FixedIngestionProvider(assertions=[ExtractedAssertion(text="Assertion B.", epistemic_status="direct")]),
        state_dir=state_dir,
    )
    return result_a.proposal_ids[0], result_b.proposal_ids[0]


def test_list_proposals_filters_by_status(vault_root, state_dir, tmp_path):
    """TC-UC011-01."""
    proposal_a, proposal_b = _ingest_two_assertions(vault_root, state_dir, tmp_path)
    accept_proposal(vault_root, "PERSONAL", proposal_a, reviewer_id="cleo")

    proposed = list_proposals(vault_root, "PERSONAL", status="PROPOSED")
    accepted = list_proposals(vault_root, "PERSONAL", status="ACCEPTED")
    everything = list_proposals(vault_root, "PERSONAL")

    assert {s.id for s in proposed} == {proposal_b}
    assert {s.id for s in accepted} == {proposal_a}
    assert {s.id for s in everything} == {proposal_a, proposal_b}


def test_get_proposal_resolves_linked_source_content_exactly(vault_root, state_dir, tmp_path):
    """TC-UC014-01: get_proposal's resolved source content matches the
    original ingested source byte-for-byte - the testable provenance/
    retrieval slice behind UC-014's goal (real answer generation is not
    implemented)."""
    source_path = tmp_path / "novel.md"
    original_content = "The original manuscript text, verbatim."
    source_path.write_text(original_content, encoding="utf-8")

    result = ingest_source(vault_root, "FICTION", source_path, FixedIngestionProvider(), state_dir=state_dir)
    proposal_id = result.proposal_ids[0]

    detail = get_proposal(vault_root, "FICTION", proposal_id)

    assert detail.source_body == original_content


def test_edit_proposal_then_accept_reflects_edited_content_with_history(vault_root, state_dir, source_file):
    """TC-UC011-02."""
    result = ingest_source(vault_root, "PERSONAL", source_file, FixedIngestionProvider(), state_dir=state_dir)
    proposal_id = result.proposal_ids[0]
    original_body = read_frontmatter(
        vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    )[1]

    edit_result = edit_proposal(
        vault_root, "PERSONAL", proposal_id, reviewer_id="cleo", body="Edited assertion text."
    )

    assert edit_result.archived_version == 1
    assert edit_result.archived_version_path.exists()
    archived_frontmatter, archived_body = read_frontmatter(edit_result.archived_version_path)
    assert archived_frontmatter["lifecycle_status"] == "SUPERSEDED"
    assert archived_frontmatter["superseded_by"] == "v2"
    assert archived_body == original_body

    edited_frontmatter, edited_body = read_frontmatter(
        vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert edited_frontmatter["proposal_status"] == "EDITED"
    assert edited_body == "Edited assertion text."

    accept_result = accept_proposal(vault_root, "PERSONAL", proposal_id, reviewer_id="cleo")
    canonical_path = (
        vault_root / "PERSONAL" / "assertions" / accept_result.assertion_id / f"{accept_result.assertion_id}.md"
    )
    _, canonical_body = read_frontmatter(canonical_path)
    assert canonical_body == "Edited assertion text."


def test_reject_with_reason_preserves_content_and_sets_reason(vault_root, state_dir, source_file):
    """TC-UC011-03."""
    result = ingest_source(vault_root, "PERSONAL", source_file, FixedIngestionProvider(), state_dir=state_dir)
    proposal_id = result.proposal_ids[0]
    original_body = read_frontmatter(
        vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    )[1]

    reject_result = reject_proposal(
        vault_root, "PERSONAL", proposal_id, reviewer_id="cleo", reason="Not relevant to this domain."
    )

    assert reject_result.rejection_reason == "Not relevant to this domain."
    frontmatter, body = read_frontmatter(
        vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert frontmatter["proposal_status"] == "REJECTED"
    assert frontmatter["resulting_item_id"] is None
    assert body == original_body
    assert not (vault_root / "PERSONAL" / "assertions").exists()


def test_accept_on_non_proposed_status_raises_and_leaves_files_untouched(vault_root, state_dir, source_file):
    """TC-UC011-04 (regression coverage for TASK-002's Criterion 4)."""
    result = ingest_source(vault_root, "PERSONAL", source_file, FixedIngestionProvider(), state_dir=state_dir)
    proposal_id = result.proposal_ids[0]
    accept_proposal(vault_root, "PERSONAL", proposal_id, reviewer_id="cleo")

    try:
        accept_proposal(vault_root, "PERSONAL", proposal_id, reviewer_id="cleo")
        assert False, "expected InvalidProposalStatusError"
    except InvalidProposalStatusError:
        pass

    assertions_dir = vault_root / "PERSONAL" / "assertions"
    assertion_dirs = list(assertions_dir.iterdir())
    assert len(assertion_dirs) == 1  # no duplicate canonical item created
