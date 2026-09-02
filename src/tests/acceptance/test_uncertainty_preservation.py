"""
UC-017 (Uncertainty). See specs/tests/test-plan.md, TC-UC017-01/02/03.

epistemic_status (direct|inferred|uncertain|contested) is required on every
proposal and is never silently defaulted to something implying certainty; it
is carried through unchanged into the canonical Assertion on accept. Numeric
confidence scores and contradiction-linking are NOT implemented - out of
scope here.
"""
import pytest
from _acceptance_helpers import FixedExtractionProvider, FixedIngestionProvider, read_frontmatter

from src.app.extraction.pipeline import extract_source
from src.app.extraction.providers.base import ExtractedEntity
from src.app.ingestion.pipeline import ingest_source
from src.app.ingestion.providers.base import ExtractedAssertion
from src.app.review.pipeline import accept_proposal


def test_epistemic_status_preserved_through_ingestion_and_acceptance(vault_root, state_dir, source_file):
    """TC-UC017-01."""
    provider = FixedIngestionProvider(
        assertions=[ExtractedAssertion(text="Alex might be the killer.", epistemic_status="uncertain")]
    )

    result = ingest_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)
    proposal_id = result.proposal_ids[0]

    proposal_frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert proposal_frontmatter["epistemic_status"] == "uncertain"

    accept_result = accept_proposal(vault_root, "FICTION", proposal_id, reviewer_id="cleo")
    assertion_frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "assertions" / accept_result.assertion_id / f"{accept_result.assertion_id}.md"
    )
    assert assertion_frontmatter["epistemic_status"] == "uncertain"


@pytest.mark.parametrize("epistemic_status", ["direct", "inferred", "uncertain", "contested"])
def test_all_four_epistemic_statuses_accepted_for_extraction_proposals(
    epistemic_status, vault_root, state_dir, source_file
):
    """TC-UC017-02: every value in the required vocabulary round-trips
    unchanged through extraction/, never silently coerced to another value."""
    provider = FixedExtractionProvider(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Alex",
                                   epistemic_status=epistemic_status)],
        events=[], relationships=[],
    )

    result = extract_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "completed"
    proposal_id = result.proposal_ids[0]
    frontmatter, _ = read_frontmatter(
        vault_root / "FICTION" / "proposals" / proposal_id / f"{proposal_id}.md"
    )
    assert frontmatter["epistemic_status"] == epistemic_status


def test_invalid_epistemic_status_rejected_before_any_ingestion_write(vault_root, state_dir, source_file):
    """TC-UC017-03a (ingestion): a provider reporting an epistemic_status
    outside the required vocabulary fails loudly - it is never silently
    coerced into an implied-certainty default."""
    provider = FixedIngestionProvider(
        assertions=[ExtractedAssertion(text="Alex did it.", epistemic_status="certain")]  # not a valid value
    )

    result = ingest_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert result.error is not None
    assert not (vault_root / "FICTION" / "proposals").exists() or not any(
        (vault_root / "FICTION" / "proposals").iterdir()
    )


def test_invalid_epistemic_status_rejected_before_any_extraction_write(vault_root, state_dir, source_file):
    """TC-UC017-03b (extraction): same guard, independent pipeline."""
    provider = FixedExtractionProvider(
        entities=[ExtractedEntity(local_id="e1", entity_type="person", text="Alex",
                                   epistemic_status="certain")],  # not a valid value
        events=[], relationships=[],
    )

    result = extract_source(vault_root, "FICTION", source_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert result.error is not None
