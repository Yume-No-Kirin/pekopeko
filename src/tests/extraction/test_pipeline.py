"""
Unit tests for the extraction pipeline: first-extraction contract (AC1),
duplicate detection (AC3), provider failure handling (AC4), domain
validation.
"""
import inspect
from pathlib import Path
from unittest.mock import Mock

import pytest

from _helpers import read_frontmatter

from src.app.extraction import (
    extract_source,
    ExtractionPipelineResult,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractionResult,
)
from src.app.extraction.errors import InvalidDomainError
from src.app.extraction.task_state import load_task_state


class FakeProvider:
    def __init__(self, result: ExtractionResult):
        self.result = result
        self.calls = 0

    def extract(self, text: str, context: dict) -> ExtractionResult:
        self.calls += 1
        return self.result


class FlakyProvider:
    """Fails on its first call, succeeds on every subsequent call - models a
    provider that raises after the source has already been written."""

    def __init__(self, result: ExtractionResult):
        self.result = result
        self.calls = 0

    def extract(self, text: str, context: dict) -> ExtractionResult:
        self.calls += 1
        if self.calls == 1:
            raise Exception("provider exploded")
        return self.result


def _full_extraction_result() -> ExtractionResult:
    return ExtractionResult(
        entities=[
            ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct"),
        ],
        events=[
            ExtractedEvent(
                local_id="ev1", text="Met Babbage", epistemic_status="inferred",
                starts_at="1833-06-01T00:00:00", ends_at=None,
            ),
        ],
        relationships=[
            ExtractedRelationship(
                text="Ada attended the event", epistemic_status="direct",
                relationship_type="participated_in", endpoints=["e1", "ev1"],
            ),
        ],
    )


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "test.md"
    path.write_text("# Test Document\n\nAda Lovelace met Charles Babbage in 1833.", encoding="utf-8")
    return path


def test_first_extraction_full_contract(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert isinstance(result, ExtractionPipelineResult)
    assert result.status == "completed"
    assert result.skipped_duplicate is False
    assert result.source_id is not None
    assert len(result.proposal_ids) == 3

    source_path = vault_root / "PERSONAL" / "sources" / result.source_id / f"{result.source_id}.md"
    assert source_path.exists()
    source_fm, source_body = read_frontmatter(source_path)
    assert source_fm["item_type"] == "source"
    assert source_fm["domain"] == "PERSONAL"
    assert source_fm["source_id"] == result.source_id
    assert source_fm["source_format"] == "markdown"
    assert source_fm["created_at"]
    assert source_fm["source_path"] == f"PERSONAL/sources/{result.source_id}/{result.source_id}.md"
    assert "Ada Lovelace met Charles Babbage" in source_fm["content"]

    for proposal_id in result.proposal_ids:
        proposal_path = vault_root / "PERSONAL" / "proposals" / proposal_id / f"{proposal_id}.md"
        assert proposal_path.exists()
        fm, _ = read_frontmatter(proposal_path)
        assert fm["item_type"] == "proposal"
        assert fm["domain"] == "PERSONAL"
        assert fm["proposal_status"] == "PROPOSED"
        assert fm["provenance"]["source_id"] == result.source_id
        assert fm["provenance"]["extraction_provider"] == "FakeProvider"
        assert fm["proposed_item_type"] in {"entity", "event", "relationship"}
        assert fm["epistemic_status"] in {"direct", "inferred", "uncertain", "contested"}
        assert "valid_from" in fm
        assert "valid_until" in fm


def test_duplicate_detection(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result1 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result1.status == "completed"
    assert provider.calls == 1

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "skipped_duplicate"
    assert result2.skipped_duplicate is True
    assert result2.source_id == result1.source_id
    assert result2.proposal_ids == []
    # No second call to the provider for a duplicate.
    assert provider.calls == 1

    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert len(list(proposals_dir.iterdir())) == 3


def test_provider_failure_handling(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = Mock()
    provider.extract.side_effect = Exception("provider exploded")

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert result.error is not None
    assert "provider exploded" in result.error

    # Source file was written before the provider call and is left in place,
    # untouched/uncorrupted - it is a complete write, not a partial one.
    source_path = vault_root / "PERSONAL" / "sources" / result.source_id / f"{result.source_id}.md"
    assert source_path.exists()

    # No proposal files were written.
    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert not proposals_dir.exists() or len(list(proposals_dir.iterdir())) == 0

    # The original input file is untouched.
    assert "Ada Lovelace" in source_file.read_text(encoding="utf-8")


def test_domain_validation(tmp_path, source_file):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    with pytest.raises(InvalidDomainError):
        extract_source(vault_root, "NOT_A_DOMAIN", source_file, provider, state_dir=state_dir)

    assert not vault_root.exists()


def test_default_state_dir_used_when_not_provided(tmp_path, source_file, monkeypatch):
    # Override via PEKOPEKO_TASK_STATE_DIR so this never touches the real
    # home directory (AGENTS.md: tests must never write outside their own
    # temp directory).
    fake_root = tmp_path / "fake_home_state"
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(fake_root))

    vault_root = tmp_path / "vault"
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", source_file, provider)

    assert result.status == "completed"
    fake_default = fake_root / "extraction"
    assert fake_default.exists()
    assert list(fake_default.glob("extract-*.json"))


def test_unregistered_extension_fails_via_outer_handler(tmp_path):
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    unsupported_file = tmp_path / "test.pdf"
    unsupported_file.write_text("not markdown", encoding="utf-8")
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", unsupported_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert "No reader registered" in result.error
    assert not vault_root.exists()


def _last_task_state(state_dir):
    state_files = sorted(state_dir.glob("extract-*.json"), key=lambda p: p.stat().st_mtime)
    assert state_files
    return load_task_state(state_dir, state_files[-1].stem)


def test_extract_source_signature_unchanged():
    """TASK-001b AC7: extract_source's public parameter list is unchanged, except for
    TASK-007's additive, backward-compatible optional task_id parameter."""
    sig = inspect.signature(extract_source)
    assert list(sig.parameters.keys()) == [
        'vault_root', 'domain', 'source_path', 'provider', 'state_dir', 'task_id'
    ]
    assert sig.parameters['task_id'].default is None


def test_successful_extraction_event_sequence(tmp_path, source_file):
    """TASK-001b AC2: a successful extract_source call produces an
    equivalent, independently-implemented events sequence for its own steps."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result.status == "completed"

    loaded = _last_task_state(state_dir)
    messages = [e.message for e in loaded.events]

    assert messages == [
        "Extraction task started",
        "Source content read",
        "No duplicate found, continuing extraction",
        "Source file written",
        "Provider extraction call started",
        "Provider extraction call finished",
        "Proposal written",
        "Proposal written",
        "Proposal written",
        "Extraction task completed",
    ]
    assert all(e.timestamp for e in loaded.events)
    assert loaded.events[-1].level == "success"

    proposed_types = [
        e.details["proposed_item_type"] for e in loaded.events if e.message == "Proposal written"
    ]
    assert proposed_types == ["entity", "event", "relationship"]


def test_provider_failure_appends_warning_event_before_failed(tmp_path, source_file):
    """TASK-001b AC3: a simulated provider failure appends a warning-level
    event describing the failure before the task is marked failed."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = Mock()
    provider.extract.side_effect = Exception("provider exploded")

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result.status == "failed"

    loaded = _last_task_state(state_dir)
    assert loaded.status == "failed"

    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert "provider exploded" in warning_events[0].details["error"]
    assert loaded.events[-1] is warning_events[0]


def test_duplicate_extraction_event_sequence(tmp_path, source_file):
    """TASK-001b AC4: a duplicate-source extraction (skipped_duplicate)
    appends an event describing the duplicate detection instead of the
    full success sequence."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    files_before_second_call = set(state_dir.glob("extract-*.json"))
    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "skipped_duplicate"

    new_state_file = (set(state_dir.glob("extract-*.json")) - files_before_second_call).pop()
    loaded = load_task_state(state_dir, new_state_file.stem)
    messages = [e.message for e in loaded.events]
    assert messages == [
        "Extraction task started",
        "Source content read",
        "Duplicate source detected, skipping extraction",
    ]


def test_provider_zero_output_failure(tmp_path, source_file):
    """TASK-001c AC4: a provider raising on zero output fails the task with
    the diagnostic in the error; no Proposal files are written."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = Mock()
    provider.extract.side_effect = Exception(
        "Failed to extract entities/events/relationships using Ollama: Ollama "
        "returned 0 entities/events/relationships (done_reason='length', "
        "model='gpt-oss:20b', response_chars=0)"
    )

    result = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert "done_reason='length'" in result.error
    assert result.proposal_ids == []
    proposals_dir = vault_root / "PERSONAL" / "proposals"
    assert not proposals_dir.exists() or len(list(proposals_dir.iterdir())) == 0


def test_retry_after_failure_calls_provider_again_and_completes(tmp_path, source_file):
    """TASK-001d AC1/AC3: a first extract_source attempt that fails after the
    source file is written, followed by a second attempt on the same
    content, calls the provider again (no skip) and completes."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FlakyProvider(_full_extraction_result())

    result1 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result1.status == "failed"

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "completed"
    assert len(result2.proposal_ids) == 3
    assert provider.calls == 2


def test_duplicate_still_skips_after_prior_completed_task(tmp_path, source_file):
    """TASK-001d AC2/AC3: a genuine duplicate (a prior attempt on the same
    source content already reached status == 'completed') still returns
    skipped_duplicate without calling the provider again - non-regression of
    current behavior, with the retry-capable code path in place."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FakeProvider(_full_extraction_result())

    result1 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result1.status == "completed"

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "skipped_duplicate"
    assert result2.source_id == result1.source_id
    assert provider.calls == 1


def test_retry_does_not_rewrite_source_file(tmp_path, source_file):
    """TASK-001d AC4: the reused-source-on-retry path does not rewrite
    sources/<id>/<id>.md - content/mtime unchanged from the first, failed
    attempt's write."""
    import time
    from src.app.extraction import storage

    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FlakyProvider(_full_extraction_result())

    result1 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result1.status == "failed"

    content = source_file.read_text(encoding="utf-8")
    source_id = storage._generate_source_id(content)
    written_source_path = vault_root / "PERSONAL" / "sources" / source_id / f"{source_id}.md"
    assert written_source_path.exists()
    content_before = written_source_path.read_bytes()
    mtime_before = written_source_path.stat().st_mtime_ns

    time.sleep(0.01)

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "completed"

    content_after = written_source_path.read_bytes()
    mtime_after = written_source_path.stat().st_mtime_ns

    assert content_after == content_before
    assert mtime_after == mtime_before


def test_retry_after_failure_event_message_distinct(tmp_path, source_file):
    """TASK-001d AC5: append_task_event's log for a retry-after-failure
    attempt contains a distinct event message identifying it as a retry
    reusing an existing source, different from both the real-duplicate-skip
    message and the fresh-write message."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    provider = FlakyProvider(_full_extraction_result())

    extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    files_before_second_call = set(state_dir.glob("extract-*.json"))

    result2 = extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)
    assert result2.status == "completed"

    new_state_file = (set(state_dir.glob("extract-*.json")) - files_before_second_call).pop()
    loaded = load_task_state(state_dir, new_state_file.stem)

    messages = [e.message for e in loaded.events]
    assert "Existing source reused, retrying extraction" in messages
    assert "Duplicate source detected, skipping extraction" not in messages
    assert "Source file written" not in messages


def test_empty_source_file_fails_before_provider_call(tmp_path):
    """TASK-001c AC5: an empty/whitespace-only source file fails the task
    with a distinct error, without ever calling the provider."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("   \n\n  ", encoding="utf-8")
    provider = FakeProvider(_full_extraction_result())

    result = extract_source(vault_root, "PERSONAL", empty_file, provider, state_dir=state_dir)

    assert result.status == "failed"
    assert result.error == "Source file is empty"
    assert provider.calls == 0

    loaded = _last_task_state(state_dir)
    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert warning_events[0].message == "Source file is empty"
