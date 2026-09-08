"""
TASK-005: pipeline.accept_proposal for entity/event/relationship proposals,
including relationship endpoint resolution (acceptance criteria 1-4, 8, 9).
"""
import pytest

from src.app.review import pipeline, storage
from src.app.review.errors import InvalidProposalStatusError, UnresolvedRelationshipEndpointError
from src.app.review.frontmatter import parse_frontmatter


def test_accept_entity_proposal_writes_canonical_entity_file(tmp_path, make_entity_proposal_file):
    proposal_id, _ = make_entity_proposal_file(
        domain="PERSONAL", entity_type="person", epistemic_status="inferred", body="Ada Lovelace."
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path.exists()
    assert result.assertion_path.parent.parent.name == "entities"
    entity_frontmatter, entity_body = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert entity_frontmatter["id"] == result.assertion_id
    assert entity_frontmatter["type"] == "entity"
    assert entity_frontmatter["domain"] == "PERSONAL"
    assert entity_frontmatter["entity_type"] == "person"
    assert entity_frontmatter["epistemic_status"] == "inferred"
    assert entity_frontmatter["lifecycle_status"] == "ACTIVE"
    assert entity_frontmatter["provenance"]["proposal_id"] == proposal_id
    assert entity_frontmatter["provenance"]["reviewed_by"] == "reviewer-1"
    assert entity_body == "Ada Lovelace."

    proposal_frontmatter, _ = parse_frontmatter(
        (tmp_path / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md").read_text(encoding="utf-8")
    )
    assert proposal_frontmatter["proposal_status"] == "ACCEPTED"
    assert proposal_frontmatter["resulting_item_id"] == result.assertion_id


def test_accept_event_proposal_writes_canonical_event_file_with_temporal_bounds(
    tmp_path, make_event_proposal_file
):
    proposal_id, _ = make_event_proposal_file(
        domain="PERSONAL", starts_at="1833-06-01T00:00:00", ends_at="1833-06-02T00:00:00"
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path.parent.parent.name == "events"
    event_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert event_frontmatter["type"] == "event"
    assert event_frontmatter["starts_at"] == "1833-06-01T00:00:00"
    assert event_frontmatter["ends_at"] == "1833-06-02T00:00:00"


def test_accept_relationship_proposal_resolves_accepted_and_passthrough_endpoints(
    tmp_path, make_entity_proposal_file, make_relationship_proposal_file
):
    entity_proposal_id, _ = make_entity_proposal_file(domain="PERSONAL")
    entity_result = pipeline.accept_proposal(tmp_path, "PERSONAL", entity_proposal_id, "reviewer-1")

    relationship_proposal_id, _ = make_relationship_proposal_file(
        domain="PERSONAL",
        relationship_type="attended",
        endpoints=[entity_proposal_id, "entity-existing-venue-123"],
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", relationship_proposal_id, "reviewer-1")

    assert result.assertion_path.parent.parent.name == "relationships"
    rel_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert rel_frontmatter["type"] == "relationship"
    assert rel_frontmatter["relationship_type"] == "attended"
    # entity_proposal_id resolved to its canonical id; the second endpoint has
    # no matching proposal so it passes through unchanged (V1 simplification).
    assert rel_frontmatter["endpoints"] == [entity_result.assertion_id, "entity-existing-venue-123"]


def test_accept_relationship_endpoint_referencing_another_relationship_proposal(
    tmp_path, make_relationship_proposal_file
):
    inner_id, _ = make_relationship_proposal_file(domain="PERSONAL", endpoints=["a", "b"])
    inner_result = pipeline.accept_proposal(tmp_path, "PERSONAL", inner_id, "reviewer-1")

    outer_id, _ = make_relationship_proposal_file(domain="PERSONAL", endpoints=[inner_id, "c"])
    outer_result = pipeline.accept_proposal(tmp_path, "PERSONAL", outer_id, "reviewer-1")

    rel_frontmatter, _ = parse_frontmatter(outer_result.assertion_path.read_text(encoding="utf-8"))
    assert rel_frontmatter["endpoints"] == [inner_result.assertion_id, "c"]


def test_accept_relationship_blocked_by_unaccepted_endpoint_raises_and_writes_nothing(
    tmp_path, make_entity_proposal_file, make_relationship_proposal_file
):
    entity_proposal_id, entity_proposal_file = make_entity_proposal_file(domain="PERSONAL")
    original_entity_content = entity_proposal_file.read_text(encoding="utf-8")

    relationship_proposal_id, relationship_proposal_file = make_relationship_proposal_file(
        domain="PERSONAL", endpoints=[entity_proposal_id, "some-other-id"]
    )

    with pytest.raises(UnresolvedRelationshipEndpointError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", relationship_proposal_id, "reviewer-1")

    # AC4: relationship proposal stays PROPOSED, no canonical relationship written.
    relationships_dir = tmp_path / "PERSONAL" / "relationships"
    assert not relationships_dir.exists() or list(relationships_dir.iterdir()) == []
    relationship_frontmatter, _ = parse_frontmatter(relationship_proposal_file.read_text(encoding="utf-8"))
    assert relationship_frontmatter["proposal_status"] == "PROPOSED"

    # AC8: no auto-cascade - the endpoint's own still-PROPOSED proposal is untouched.
    assert entity_proposal_file.read_text(encoding="utf-8") == original_entity_content


def test_accept_relationship_endpoint_rejected_is_also_unresolved(
    tmp_path, make_entity_proposal_file, make_relationship_proposal_file
):
    entity_proposal_id, _ = make_entity_proposal_file(domain="PERSONAL")
    pipeline.reject_proposal(tmp_path, "PERSONAL", entity_proposal_id, "reviewer-1")

    relationship_proposal_id, _ = make_relationship_proposal_file(
        domain="PERSONAL", endpoints=[entity_proposal_id, "some-other-id"]
    )

    with pytest.raises(UnresolvedRelationshipEndpointError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", relationship_proposal_id, "reviewer-1")


def test_accept_entity_proposal_write_failure_leaves_proposal_untouched(
    tmp_path, monkeypatch, make_entity_proposal_file
):
    proposal_id, proposal_file = make_entity_proposal_file(domain="PERSONAL")
    original_content = proposal_file.read_text(encoding="utf-8")

    def boom(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(storage, "write_entity_file", boom)

    with pytest.raises(OSError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert proposal_file.read_text(encoding="utf-8") == original_content
    entities_dir = tmp_path / "PERSONAL" / "entities"
    assert not entities_dir.exists() or list(entities_dir.iterdir()) == []


@pytest.mark.parametrize("make_fixture_name", ["make_entity_proposal_file", "make_event_proposal_file"])
def test_double_accept_raises_for_new_types(tmp_path, request, make_fixture_name):
    make_fixture = request.getfixturevalue(make_fixture_name)
    proposal_id, _ = make_fixture(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_double_accept_raises_for_relationship(tmp_path, make_relationship_proposal_file):
    proposal_id, _ = make_relationship_proposal_file(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


def test_accept_then_reject_raises_for_entity(tmp_path, make_entity_proposal_file):
    proposal_id, _ = make_entity_proposal_file(domain="PERSONAL")
    pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    with pytest.raises(InvalidProposalStatusError):
        pipeline.reject_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-2")


# TASK-005a: ADI-012 adoption by entity/event/relationship - accept_proposal reads
# proposed_path_segments from the accepted proposal for these three types too.

def test_accept_entity_proposal_writes_segmented_path_when_proposed_path_segments_present(
    tmp_path, make_entity_proposal_file
):
    """AC4."""
    proposal_id, _ = make_entity_proposal_file(
        domain="PERSONAL", proposed_path_segments=["mythologie", "personnages"]
    )

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path == storage.entity_path(
        tmp_path, "PERSONAL", result.assertion_id, path_segments=["mythologie", "personnages"]
    )
    assert result.assertion_path.exists()


def test_accept_event_proposal_writes_segmented_path_when_proposed_path_segments_present(
    tmp_path, make_event_proposal_file
):
    """AC4."""
    proposal_id, _ = make_event_proposal_file(domain="PERSONAL", proposed_path_segments=["guerre"])

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path == storage.event_path(
        tmp_path, "PERSONAL", result.assertion_id, path_segments=["guerre"]
    )
    assert result.assertion_path.exists()


def test_accept_relationship_proposal_writes_segmented_path_when_proposed_path_segments_present(
    tmp_path, make_relationship_proposal_file
):
    """AC4."""
    proposal_id, _ = make_relationship_proposal_file(domain="PERSONAL", proposed_path_segments=["famille"])

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path == storage.relationship_path(
        tmp_path, "PERSONAL", result.assertion_id, path_segments=["famille"]
    )
    assert result.assertion_path.exists()


@pytest.mark.parametrize(
    "make_fixture_name",
    ["make_entity_proposal_file", "make_event_proposal_file", "make_relationship_proposal_file"],
)
def test_accept_writes_plain_path_when_proposed_path_segments_absent(tmp_path, request, make_fixture_name):
    """AC4/AC5: field absent (proposal predating TASK-005a) writes to the plain
    fixed path - no regression, no error."""
    make_fixture = request.getfixturevalue(make_fixture_name)
    proposal_id, _ = make_fixture(domain="PERSONAL")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    # Plain path has exactly 2 path components below the type-plural folder:
    # <item_id>/<item_id>.md - no extra taxonomy segment directories.
    assert result.assertion_path.parent.parent.name in ("entities", "events", "relationships")
    assert result.assertion_path.parent.name == result.assertion_id


def test_accept_entity_proposal_writes_plain_path_when_proposed_path_segments_null(
    tmp_path, make_entity_proposal_file
):
    """AC4/AC5: field explicitly null behaves the same as absent."""
    proposal_id, _ = make_entity_proposal_file(domain="PERSONAL", proposed_path_segments=None)

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path == storage.entity_path(tmp_path, "PERSONAL", result.assertion_id)


# TASK-014a: context field (ADI-016) - symmetric for entity/event/relationship

@pytest.mark.parametrize(
    "make_fixture_name,path_fn",
    [
        ("make_entity_proposal_file", storage.entity_path),
        ("make_event_proposal_file", storage.event_path),
        ("make_relationship_proposal_file", storage.relationship_path),
    ],
)
def test_accept_writes_context_segmented_path_and_frontmatter(tmp_path, request, make_fixture_name, path_fn):
    """AC6: context in frontmatter writes to the context-segmented path and is
    reflected in the canonical file's own frontmatter, for entity/event/relationship."""
    make_fixture = request.getfixturevalue(make_fixture_name)
    proposal_id, _ = make_fixture(domain="PERSONAL", context="tatouages")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path == path_fn(tmp_path, "PERSONAL", result.assertion_id, context="tatouages")
    assert result.assertion_path.exists()
    item_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert item_frontmatter["context"] == "tatouages"


@pytest.mark.parametrize(
    "make_fixture_name",
    ["make_entity_proposal_file", "make_event_proposal_file", "make_relationship_proposal_file"],
)
def test_accept_writes_plain_path_and_null_context_when_context_absent(tmp_path, request, make_fixture_name):
    """AC7: context absent writes the plain path, no regression, for
    entity/event/relationship."""
    make_fixture = request.getfixturevalue(make_fixture_name)
    proposal_id, _ = make_fixture(domain="PERSONAL")

    result = pipeline.accept_proposal(tmp_path, "PERSONAL", proposal_id, "reviewer-1")

    assert result.assertion_path.parent.name == result.assertion_id
    item_frontmatter, _ = parse_frontmatter(result.assertion_path.read_text(encoding="utf-8"))
    assert item_frontmatter["context"] is None
