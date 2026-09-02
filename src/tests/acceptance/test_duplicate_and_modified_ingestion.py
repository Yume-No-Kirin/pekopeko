"""
UC-016 (Duplicate/Repeated Ingestion) and UC-003 (Novel Change & Staleness,
thin slice). See specs/tests/test-plan.md, TC-UC016-01/02, TC-UC003-01.

UC-016 is directly implemented (INV-020) for both pipelines: re-ingesting
identical content never calls the provider a second time and creates no new
files. UC-003's testable slice is much thinner: a *modified* source produces
an entirely independent new Source (new content hash) with no linkage or
staleness marking back to the old one - real current behavior, not the full
UC-003 vision (true staleness tracking / CAP-CORE-006 is not implemented).
"""
from _acceptance_helpers import FixedExtractionProvider, FixedIngestionProvider

from src.app.extraction.pipeline import extract_source
from src.app.ingestion.pipeline import ingest_source


def _proposal_ids_on_disk(vault_root, domain):
    proposals_dir = vault_root / domain / "proposals"
    if not proposals_dir.exists():
        return set()
    return {p.name for p in proposals_dir.iterdir() if p.is_dir()}


def _source_ids_on_disk(vault_root, domain):
    sources_dir = vault_root / domain / "sources"
    if not sources_dir.exists():
        return set()
    return {s.name for s in sources_dir.iterdir() if s.is_dir()}


def test_duplicate_ingestion_creates_no_new_files_and_skips_provider_call(vault_root, state_dir, source_file):
    """TC-UC016-01 (ingestion): re-ingesting identical content is a no-op
    beyond the first call - provider.extract() is called exactly once."""
    provider = FixedIngestionProvider()

    first = ingest_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert first.status == "completed"
    proposal_ids_after_first = _proposal_ids_on_disk(vault_root, "PERSONAL")
    source_ids_after_first = _source_ids_on_disk(vault_root, "PERSONAL")

    second = ingest_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert second.status == "skipped_duplicate"
    assert second.skipped_duplicate is True
    assert second.source_id == first.source_id
    assert len(provider.calls) == 1  # never called for the duplicate attempt
    assert _proposal_ids_on_disk(vault_root, "PERSONAL") == proposal_ids_after_first
    assert _source_ids_on_disk(vault_root, "PERSONAL") == source_ids_after_first


def test_duplicate_extraction_creates_no_new_files_and_skips_provider_call(vault_root, state_dir, source_file):
    """TC-UC016-02 (extraction): same guarantee as above, independent pipeline."""
    provider = FixedExtractionProvider()

    first = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert first.status == "completed"
    proposal_ids_after_first = _proposal_ids_on_disk(vault_root, "PERSONAL")

    second = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert second.status == "skipped_duplicate"
    assert second.skipped_duplicate is True
    assert second.source_id == first.source_id
    assert len(provider.calls) == 1
    assert _proposal_ids_on_disk(vault_root, "PERSONAL") == proposal_ids_after_first


def test_modified_source_produces_independent_new_source_no_linkage(vault_root, state_dir, tmp_path):
    """TC-UC003-01: a modified source is treated as a brand new, independent
    source (different content hash) - the old Source/Proposals are left
    exactly as they were, and nothing on the new Source/Proposals links back
    to or supersedes the old ones. This documents the real (thin) current
    behavior; true staleness propagation is not implemented."""
    provider = FixedIngestionProvider()
    source_path = tmp_path / "novel.md"

    source_path.write_text("Version one of the manuscript.", encoding="utf-8")
    first = ingest_source(vault_root, "FICTION", source_path, provider, state_dir=state_dir)
    assert first.status == "completed"
    first_source_path = vault_root / "FICTION" / "sources" / first.source_id / f"{first.source_id}.md"
    first_source_content_before = first_source_path.read_text(encoding="utf-8")

    source_path.write_text("Version two of the manuscript - substantially rewritten.", encoding="utf-8")
    second = ingest_source(vault_root, "FICTION", source_path, provider, state_dir=state_dir)

    assert second.status == "completed"
    assert second.source_id != first.source_id
    assert first_source_path.exists()
    assert first_source_path.read_text(encoding="utf-8") == first_source_content_before  # untouched

    second_source_path = vault_root / "FICTION" / "sources" / second.source_id / f"{second.source_id}.md"
    assert second_source_path.exists()
    assert first.source_id not in second_source_path.read_text(encoding="utf-8")
