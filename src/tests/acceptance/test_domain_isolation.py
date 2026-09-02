"""
UC-009 (Cross-Domain Analysis, isolation slice) and UC-018 (Fictional
Universe Isolation, domain-level slice). See specs/tests/test-plan.md,
TC-UC009-01/02, TC-UC018-01.

Only domain-level isolation (INV-008: no operation crosses a domain boundary
implicitly) is implemented and testable. There is no "context"/sub-domain
concept in the schema (e.g. distinguishing two FICTION novels sharing a
character name) - UC-018's full goal is not covered, only the coarser
domain-level guarantee.
"""
from _acceptance_helpers import (
    FixedExtractionProvider,
    FixedIngestionProvider,
    read_frontmatter,
    write_proposal_frontmatter_file,
)

from src.app.extraction.pipeline import extract_source
from src.app.extraction.providers.base import ExtractedEntity
from src.app.ingestion.pipeline import ingest_source
from src.app.review.errors import DomainMismatchError, ProposalNotFoundError
from src.app.review.pipeline import get_proposal, list_proposals


def test_list_proposals_never_leaks_across_domains(vault_root, state_dir, tmp_path):
    """TC-UC009-01."""
    personal_source = tmp_path / "personal.md"
    personal_source.write_text("A personal note.", encoding="utf-8")
    fiction_source = tmp_path / "fiction.md"
    fiction_source.write_text("A fiction excerpt.", encoding="utf-8")

    personal_result = ingest_source(vault_root, "PERSONAL", personal_source, FixedIngestionProvider(),
                                     state_dir=state_dir)
    fiction_result = ingest_source(vault_root, "FICTION", fiction_source, FixedIngestionProvider(),
                                    state_dir=state_dir)

    personal_summaries = list_proposals(vault_root, "PERSONAL")
    fiction_summaries = list_proposals(vault_root, "FICTION")

    personal_ids = {s.id for s in personal_summaries}
    fiction_ids = {s.id for s in fiction_summaries}

    assert personal_ids == set(personal_result.proposal_ids)
    assert fiction_ids == set(fiction_result.proposal_ids)
    assert personal_ids.isdisjoint(fiction_ids)
    assert set(fiction_result.proposal_ids).isdisjoint(personal_ids)


def test_get_proposal_under_wrong_domain_path_is_not_found(vault_root, state_dir, source_file):
    """TC-UC009-02a: a proposal only exists under its own domain's folder -
    looking it up under a different domain path is a plain not-found, since
    the two domains are entirely separate folder trees."""
    result = ingest_source(vault_root, "FICTION", source_file, FixedIngestionProvider(), state_dir=state_dir)
    proposal_id = result.proposal_ids[0]

    try:
        get_proposal(vault_root, "PERSONAL", proposal_id)
        assert False, "expected ProposalNotFoundError"
    except ProposalNotFoundError:
        pass


def test_get_proposal_with_mismatched_frontmatter_domain_is_rejected(vault_root):
    """TC-UC009-02b: a corrupted/hand-edited proposal whose folder domain and
    frontmatter `domain` field disagree is rejected explicitly
    (DomainMismatchError), rather than silently trusting either value."""
    proposal_id = "prop-mismatch-test"
    path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
    write_proposal_frontmatter_file(
        path,
        {
            "id": proposal_id,
            "type": "proposal",
            "domain": "FICTION",  # disagrees with the PERSONAL folder path below
            "proposal_status": "PROPOSED",
            "proposed_item_type": "assertion",
            "epistemic_status": "direct",
            "created_at": "2026-01-01T00:00:00",
            "valid_from": "2026-01-01T00:00:00",
            "valid_until": None,
            "provenance": {"source_id": "src-does-not-matter", "extraction_provider": "test"},
        },
        "Some text.",
    )

    try:
        get_proposal(vault_root, "PERSONAL", proposal_id)
        assert False, "expected DomainMismatchError"
    except DomainMismatchError:
        pass


def test_same_name_entities_across_two_extraction_calls_never_merge(vault_root, state_dir, tmp_path):
    """TC-UC018-01: two separately-ingested sources, both naming an entity
    "Alex" in the same FICTION domain, never get merged/deduplicated by name
    - each extraction call produces its own independent proposal_id. This
    demonstrates the system doesn't accidentally conflate same-named
    entities; it does NOT demonstrate true universe/context isolation (no
    such concept exists in the schema - see specs/tests/test-plan.md)."""
    novel_a_source = tmp_path / "novel_a.md"
    novel_a_source.write_text("Novel A: Alex is a knight.", encoding="utf-8")
    novel_b_source = tmp_path / "novel_b.md"
    novel_b_source.write_text("Novel B: Alex is a spaceship pilot.", encoding="utf-8")

    provider_a = FixedExtractionProvider(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Alex", epistemic_status="direct")],
        events=[], relationships=[],
    )
    provider_b = FixedExtractionProvider(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Alex", epistemic_status="direct")],
        events=[], relationships=[],
    )

    result_a = extract_source(vault_root, "FICTION", novel_a_source, provider_a, state_dir=state_dir)
    result_b = extract_source(vault_root, "FICTION", novel_b_source, provider_b, state_dir=state_dir)

    assert result_a.status == "completed"
    assert result_b.status == "completed"
    assert len(result_a.proposal_ids) == 1
    assert len(result_b.proposal_ids) == 1
    assert result_a.proposal_ids[0] != result_b.proposal_ids[0]  # independent IDs, never merged

    frontmatter_a, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / result_a.proposal_ids[0] / f"{result_a.proposal_ids[0]}.md"
    )
    frontmatter_b, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / result_b.proposal_ids[0] / f"{result_b.proposal_ids[0]}.md"
    )
    assert frontmatter_a["provenance"]["source_id"] != frontmatter_b["provenance"]["source_id"]
