"""
UC-001 (Novel Ingestion) - the flagship SOURCE -> PROPOSAL -> REVIEW ->
CANONICAL round trip, deterministic layer. See specs/tests/test-plan.md,
section UC-001, TC-UC001-01/02.

Assertions (ingestion/) and, since TASK-003a + TASK-005, entity/event/
relationship (extraction/) both go all the way to a canonical item.
"""
from _acceptance_helpers import FixedExtractionProvider, FixedIngestionProvider, read_frontmatter

from src.app.extraction.pipeline import extract_source
from src.app.ingestion.pipeline import ingest_source
from src.app.review.pipeline import accept_proposal


def test_assertion_full_round_trip_creates_traceable_canonical_item(vault_root, state_dir, source_file):
    """TC-UC001-01: source -> proposal -> accept -> canonical, provenance chain intact."""
    provider = FixedIngestionProvider()

    result = ingest_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "completed"
    assert result.source_id is not None
    assert len(result.proposal_ids) == 1
    proposal_id = result.proposal_ids[0]

    proposal_frontmatter, proposal_body = read_frontmatter(
        vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert proposal_frontmatter["proposal_status"] == "PROPOSED"
    assert proposal_frontmatter["proposed_item_type"] == "assertion"
    assert proposal_frontmatter["epistemic_status"] == "direct"
    assert proposal_frontmatter["provenance"]["source_id"] == result.source_id
    assert proposal_body == "Alex is the protagonist of the story."

    accept_result = accept_proposal(vault_root, "FICTION", proposal_id, reviewer_id="cleo")

    canonical_path = vault_root / "FICTION" / "assertions" / accept_result.assertion_id / f"{accept_result.assertion_id}.md"
    assert canonical_path.exists()
    assertion_frontmatter, assertion_body = read_frontmatter(canonical_path)
    assert assertion_frontmatter["provenance"]["proposal_id"] == proposal_id
    assert assertion_frontmatter["provenance"]["source_id"] == result.source_id
    assert assertion_frontmatter["provenance"]["reviewed_by"] == "cleo"
    assert assertion_frontmatter["epistemic_status"] == "direct"
    assert assertion_body == proposal_body

    updated_proposal_frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert updated_proposal_frontmatter["proposal_status"] == "ACCEPTED"
    assert updated_proposal_frontmatter["resulting_item_id"] == accept_result.assertion_id


def test_entity_event_relationship_full_round_trip_creates_traceable_canonical_items(
    vault_root, state_dir, source_file
):
    """TC-UC001-02: entity/event/relationship proposals are created (SOURCE ->
    PROPOSAL half of UC-001), then accepted all the way to canonical items,
    including relationship endpoint resolution (ADI-003) - since TASK-003a
    (extraction proposals now carry the id/type fields review/ requires) and
    TASK-005 (review/ accepts entity/event/relationship proposals)."""
    provider = FixedExtractionProvider()

    result = extract_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "completed"
    assert len(result.proposal_ids) == 4  # 2 entities + 1 event + 1 relationship

    proposals_by_type = {}
    for proposal_id in result.proposal_ids:
        frontmatter, _ = read_frontmatter(
            vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
        )
        assert frontmatter["proposal_status"] == "PROPOSED"
        assert frontmatter["provenance"]["source_id"] == result.source_id
        proposals_by_type.setdefault(frontmatter["proposed_item_type"], []).append(proposal_id)

    assert set(proposals_by_type) == {"entity", "event", "relationship"}
    assert len(proposals_by_type["entity"]) == 2

    # Accept both entities and the event first - the relationship's endpoints
    # (the two entities' proposal_ids, per extraction/'s local_id resolution)
    # must already be ACCEPTED before the relationship itself can resolve.
    entity_canonical_ids = {}
    for proposal_id in proposals_by_type["entity"]:
        entity_result = accept_proposal(vault_root, "FICTION", proposal_id, reviewer_id="cleo")
        entity_canonical_ids[proposal_id] = entity_result.assertion_id
        entity_frontmatter, _ = read_frontmatter(entity_result.assertion_path)
        assert entity_frontmatter["type"] == "entity"
        assert entity_frontmatter["provenance"]["proposal_id"] == proposal_id

    event_proposal_id = proposals_by_type["event"][0]
    event_result = accept_proposal(vault_root, "FICTION", event_proposal_id, reviewer_id="cleo")
    event_frontmatter, _ = read_frontmatter(event_result.assertion_path)
    assert event_frontmatter["type"] == "event"
    assert event_frontmatter["starts_at"] == "2026-01-01T00:00:00"

    relationship_proposal_id = proposals_by_type["relationship"][0]
    relationship_proposal_frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / relationship_proposal_id / f"{relationship_proposal_id}.md"
    )
    endpoint_proposal_ids = relationship_proposal_frontmatter["endpoints"]
    assert set(endpoint_proposal_ids) == set(entity_canonical_ids)  # resolved to entity proposal_ids by extraction/

    relationship_result = accept_proposal(vault_root, "FICTION", relationship_proposal_id, reviewer_id="cleo")
    relationship_frontmatter, _ = read_frontmatter(relationship_result.assertion_path)
    assert relationship_frontmatter["type"] == "relationship"
    assert relationship_frontmatter["relationship_type"] == "knows"
    # Endpoints replaced by resolved canonical entity ids (ADI-003), not the
    # original proposal_ids.
    assert set(relationship_frontmatter["endpoints"]) == set(entity_canonical_ids.values())

    updated_relationship_proposal_frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / relationship_proposal_id / f"{relationship_proposal_id}.md"
    )
    assert updated_relationship_proposal_frontmatter["proposal_status"] == "ACCEPTED"
    assert updated_relationship_proposal_frontmatter["resulting_item_id"] == relationship_result.assertion_id
