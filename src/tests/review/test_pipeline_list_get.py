"""
Unit tests for pipeline.list_proposals and pipeline.get_proposal
(acceptance criteria 6, 7).
"""
import pytest

from src.app.review import pipeline
from src.app.review.errors import (
    DomainMismatchError,
    ProposalNotFoundError,
    SourceNotFoundError,
    ValidationError,
)


def test_list_proposals_filters_by_status(tmp_path, make_proposal_file):
    proposed_id, _ = make_proposal_file(domain="PERSONAL", status="PROPOSED")
    make_proposal_file(domain="PERSONAL", status="ACCEPTED")

    proposed_only = pipeline.list_proposals(tmp_path, "PERSONAL", status="PROPOSED")

    assert [p.id for p in proposed_only] == [proposed_id]


def test_list_proposals_domain_isolation(tmp_path, make_proposal_file):
    personal_id, _ = make_proposal_file(domain="PERSONAL")
    make_proposal_file(domain="FICTION")

    personal_proposals = pipeline.list_proposals(tmp_path, "PERSONAL")

    assert [p.id for p in personal_proposals] == [personal_id]


def test_list_proposals_no_status_filter_returns_all_statuses(tmp_path, make_proposal_file):
    proposed_id, _ = make_proposal_file(domain="PERSONAL", status="PROPOSED")
    rejected_id, _ = make_proposal_file(domain="PERSONAL", status="REJECTED")

    all_proposals = pipeline.list_proposals(tmp_path, "PERSONAL")

    assert {p.id for p in all_proposals} == {proposed_id, rejected_id}


def test_list_proposals_empty_domain_returns_empty_list(tmp_path):
    assert pipeline.list_proposals(tmp_path, "PERSONAL") == []


def test_list_proposals_skips_malformed_proposal_file(tmp_path, make_proposal_file):
    good_id, _ = make_proposal_file(domain="PERSONAL")
    bad_id, bad_path = make_proposal_file(domain="PERSONAL")
    bad_path.write_text("not frontmatter at all", encoding="utf-8")

    proposals = pipeline.list_proposals(tmp_path, "PERSONAL")

    assert [p.id for p in proposals] == [good_id]


def test_list_proposals_skips_mismatched_domain_proposal(tmp_path, make_proposal_file):
    good_id, _ = make_proposal_file(domain="PERSONAL")
    make_proposal_file(domain="PERSONAL", internal_domain="FICTION")

    proposals = pipeline.list_proposals(tmp_path, "PERSONAL")

    assert [p.id for p in proposals] == [good_id]


def test_get_proposal_returns_frontmatter_and_body(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", body="The extracted assertion text.")

    detail = pipeline.get_proposal(tmp_path, "PERSONAL", proposal_id)

    assert detail.id == proposal_id
    assert detail.body == "The extracted assertion text."


def test_get_proposal_resolves_linked_source_content(tmp_path, make_proposal_file, make_source_file):
    source_id, _ = make_source_file(domain="PERSONAL", content="Original source content.")
    proposal_id, _ = make_proposal_file(domain="PERSONAL", source_id=source_id)

    detail = pipeline.get_proposal(tmp_path, "PERSONAL", proposal_id)

    assert detail.source_frontmatter["id"] == source_id
    assert detail.source_body == "Original source content."


def test_get_proposal_missing_source_raises_source_not_found(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", source_id="src-does-not-exist")

    with pytest.raises(SourceNotFoundError):
        pipeline.get_proposal(tmp_path, "PERSONAL", proposal_id)


def test_get_proposal_missing_provenance_source_id_raises_validation_error(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", provenance={"extraction_provider": "TestProvider"})

    with pytest.raises(ValidationError):
        pipeline.get_proposal(tmp_path, "PERSONAL", proposal_id)


def test_get_proposal_nonexistent_proposal_raises_not_found(tmp_path):
    with pytest.raises(ProposalNotFoundError):
        pipeline.get_proposal(tmp_path, "PERSONAL", "prop-missing")


def test_get_proposal_wrong_domain_raises_domain_mismatch(tmp_path, make_proposal_file):
    proposal_id, _ = make_proposal_file(domain="PERSONAL", internal_domain="FICTION")

    with pytest.raises(DomainMismatchError):
        pipeline.get_proposal(tmp_path, "PERSONAL", proposal_id)


# TASK-005: list_proposals/get_proposal regression for a mix of all 4 proposed_item_types

def test_list_proposals_returns_all_four_types_mixed(
    tmp_path, make_proposal_file, make_entity_proposal_file, make_event_proposal_file,
    make_relationship_proposal_file,
):
    assertion_id, _ = make_proposal_file(domain="PERSONAL")
    entity_id, _ = make_entity_proposal_file(domain="PERSONAL")
    event_id, _ = make_event_proposal_file(domain="PERSONAL")
    relationship_id, _ = make_relationship_proposal_file(domain="PERSONAL")

    proposals = pipeline.list_proposals(tmp_path, "PERSONAL")

    assert {p.id for p in proposals} == {assertion_id, entity_id, event_id, relationship_id}
    types_by_id = {p.id: p.proposed_item_type for p in proposals}
    assert types_by_id[assertion_id] == "assertion"
    assert types_by_id[entity_id] == "entity"
    assert types_by_id[event_id] == "event"
    assert types_by_id[relationship_id] == "relationship"


def test_get_proposal_returns_type_specific_fields_for_each_type(
    tmp_path, make_entity_proposal_file, make_event_proposal_file, make_relationship_proposal_file,
):
    entity_id, _ = make_entity_proposal_file(domain="PERSONAL", entity_type="place")
    event_id, _ = make_event_proposal_file(
        domain="PERSONAL", starts_at="2026-01-01T00:00:00", ends_at="2026-01-02T00:00:00"
    )
    relationship_id, _ = make_relationship_proposal_file(
        domain="PERSONAL", relationship_type="located_in", endpoints=["a", "b"]
    )

    entity_detail = pipeline.get_proposal(tmp_path, "PERSONAL", entity_id)
    event_detail = pipeline.get_proposal(tmp_path, "PERSONAL", event_id)
    relationship_detail = pipeline.get_proposal(tmp_path, "PERSONAL", relationship_id)

    assert entity_detail.frontmatter["entity_type"] == "place"
    assert event_detail.frontmatter["starts_at"] == "2026-01-01T00:00:00"
    assert event_detail.frontmatter["ends_at"] == "2026-01-02T00:00:00"
    assert relationship_detail.frontmatter["relationship_type"] == "located_in"
    assert relationship_detail.frontmatter["endpoints"] == ["a", "b"]
