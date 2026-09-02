"""
UC-001 (Novel Ingestion) - the flagship SOURCE -> PROPOSAL -> REVIEW ->
CANONICAL round trip, deterministic layer. See specs/tests/test-plan.md,
section UC-001, TC-UC001-01/02.

Assertions (ingestion/) go all the way to a canonical item, since TASK-002/
TASK-006's accept_proposal only supports proposed_item_type == "assertion".
Entity/Event/Relationship (extraction/) stop at PROPOSED and their accept
attempt is asserted to fail with UnsupportedProposalTypeError - TASK-005 is
still `backlog`, so this is a documented, regression-guarded gap rather than
an untested one (per the project's own "maquettes are the target, gaps are
flagged not cut" discipline already applied to TASK-001a/001b/007a).
"""
from _acceptance_helpers import FixedExtractionProvider, FixedIngestionProvider, read_frontmatter

from src.app.extraction.pipeline import extract_source
from src.app.ingestion.pipeline import ingest_source
from src.app.review.errors import ValidationError
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


def test_entity_event_relationship_extraction_stops_at_proposed_and_accept_is_unsupported(
    vault_root, state_dir, source_file
):
    """TC-UC001-02: entity/event/relationship proposals are created correctly
    (SOURCE -> PROPOSAL half of UC-001), but accept_proposal on any of them
    fails - TASK-005 (review for these types) is still `backlog`. This is the
    documented, testable boundary of UC-001's current coverage, not a silent
    gap.

    Real (verified) failure mode: review.errors.ValidationError, not
    UnsupportedProposalTypeError. extraction/storage.py (TASK-003) writes
    proposal frontmatter with `item_type`/no top-level `id` (its own
    deliberately independent contract), while review/storage.py's
    REQUIRED_PROPOSAL_FIELDS (TASK-002) requires `id`/`type`. Any
    extraction-produced proposal therefore fails review/'s own field
    validation before the "assertion-only" business rule is ever reached -
    a schema-level incompatibility between the two tickets' independent
    contracts, not just a not-yet-implemented business rule. Flagged here
    for Cleo; TASK-005 will need to either reconcile the field names or
    teach review/ to read both contracts. See specs/tests/test-plan.md,
    UC-001 section."""
    provider = FixedExtractionProvider()

    result = extract_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "completed"
    assert len(result.proposal_ids) == 4  # 2 entities + 1 event + 1 relationship

    proposed_item_types = set()
    for proposal_id in result.proposal_ids:
        frontmatter, _ = read_frontmatter(
            vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
        )
        assert frontmatter["proposal_status"] == "PROPOSED"
        assert frontmatter["provenance"]["source_id"] == result.source_id
        proposed_item_types.add(frontmatter["proposed_item_type"])

    assert proposed_item_types == {"entity", "event", "relationship"}

    for proposal_id in result.proposal_ids:
        try:
            accept_proposal(vault_root, "FICTION", proposal_id, reviewer_id="cleo")
            assert False, f"accept_proposal unexpectedly succeeded for {proposal_id}"
        except ValidationError:
            pass

        # No canonical item and no status change leaked out of the failed attempt.
        frontmatter, _ = read_frontmatter(
            vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
        )
        assert frontmatter["proposal_status"] == "PROPOSED"
