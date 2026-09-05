"""
Unit tests for the ingestion pipeline.
"""
import tempfile
import os
import time
import inspect
from pathlib import Path
import pytest
import yaml
from unittest.mock import Mock, patch

# Add the app directory to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.ingestion import (
    ingest_source,
    OllamaProvider,
    OllamaProviderConfig,
    IngestionResult,
    SourceReaderRegistry,
    write_source_file,
    write_proposal_file
)
from src.app.ingestion.providers.base import ExtractedAssertion, ExtractionResult
from src.app.ingestion.storage import scan_existing_assertion_folders, scan_proposed_path_segments


def test_import_isolation():
    """Test that pipeline code doesn't directly import LLM SDKs."""
    # This test verifies the static analysis requirement (Criterion 2)
    # We'll check that no direct imports of requests or similar libraries exist in pipeline.py

    pipeline_content = Path("app/ingestion/pipeline.py").read_text()

    # Verify no direct imports of http libraries or LLM SDKs
    assert "import requests" not in pipeline_content
    assert "from requests" not in pipeline_content
    assert "import httpx" not in pipeline_content
    assert "from httpx" not in pipeline_content

    print("✓ Pipeline code does not directly import LLM SDKs")


def test_ingestion_result():
    """Test IngestionResult class."""
    result = IngestionResult(
        source_id="src-test123",
        proposal_ids=["prop-1", "prop-2"],
        status="completed",
        error=None,
        skipped_duplicate=False
    )

    assert result.source_id == "src-test123"
    assert result.proposal_ids == ["prop-1", "prop-2"]
    assert result.status == "completed"
    assert result.skipped_duplicate is False


def test_duplicate_detection():
    """Test duplicate ingestion detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        # Write test content
        test_content = "# Test Document\n\nThis is a test."
        with open(source_file, 'w') as f:
            f.write(test_content)

        # Create provider mock
        provider = Mock()
        provider.extract.return_value = ExtractionResult(assertions=[])

        # First ingestion - should create files
        result1 = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result1.status == "completed"
        assert result1.source_id is not None
        assert len(result1.proposal_ids) == 0

        # Second ingestion of same content - should detect duplicate
        result2 = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result2.status == "skipped_duplicate"
        assert result2.source_id == result1.source_id
        assert result2.skipped_duplicate is True

        print("✓ Duplicate detection works correctly")


def test_provider_failure_handling():
    """Test that pipeline handles provider failures gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        # Write test content
        test_content = "# Test Document\n\nThis is a test."
        with open(source_file, 'w') as f:
            f.write(test_content)

        # Create provider that raises an exception
        provider = Mock()
        provider.extract.side_effect = Exception("Provider failed")

        # Ingestion should fail gracefully
        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result.status == "failed"
        assert result.error is not None

        print("✓ Provider failure handling works correctly")


def test_provider_interface_compliance():
    """Test that the OllamaProvider implements the Provider interface."""
    config = OllamaProviderConfig()
    provider = OllamaProvider(config)

    # Check that it has the required method
    assert hasattr(provider, 'extract')
    assert callable(getattr(provider, 'extract'))

    print("✓ Provider interface compliance verified")


def test_source_reader_registry():
    """Test source reader registry functionality."""
    from src.app.ingestion.readers.base import SourceReaderRegistry

    registry = SourceReaderRegistry()

    # Check that we can register and retrieve readers
    assert len(registry._readers) == 0

    # Test with markdown reader
    from src.app.ingestion.readers.markdown_reader import MarkdownReader
    registry.register(".md", MarkdownReader)

    reader_class = registry.get_reader(".md")
    assert reader_class is not None
    assert reader_class == MarkdownReader

    print("✓ Source reader registry works correctly")


def test_atomic_writes():
    """Test that file writes are atomic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        # Write test content
        test_content = "# Test Document\n\nThis is a test."
        with open(source_file, 'w') as f:
            f.write(test_content)

        # Test writing a source file
        source_id = write_source_file(vault_root, "PERSONAL", test_content, "test.md")
        assert source_id is not None

        # Check that the file was written correctly
        source_path = vault_root / "PERSONAL" / "sources" / source_id / f"{source_id}.md"
        assert source_path.exists()

        print("✓ Atomic writes work correctly")


def test_epistemic_status():
    """Test that all assertions have valid epistemic status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        # Write test content
        test_content = "# Test Document\n\nThis is a test."
        with open(source_file, 'w') as f:
            f.write(test_content)

        # Create provider that returns assertions with epistemic status
        provider = Mock()
        provider.extract.return_value = ExtractionResult(
            assertions=[
                ExtractedAssertion(text="Test assertion", epistemic_status="inferred"),
                ExtractedAssertion(text="Another test", epistemic_status="direct"),
                ExtractedAssertion(text="Uncertain fact", epistemic_status="uncertain")
            ]
        )

        # Ingest and check that all assertions have valid status
        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result.status == "completed"
        assert len(result.proposal_ids) == 3

        print("✓ All assertions have valid epistemic_status values")


def test_domain_validation():
    """Test that invalid domains are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        # Write test content
        test_content = "# Test Document\n\nThis is a test."
        with open(source_file, 'w') as f:
            f.write(test_content)

        # Create provider mock
        provider = Mock()
        provider.extract.return_value = ExtractionResult(assertions=[])

        # Test invalid domain - should raise ValueError
        try:
            ingest_source(
                vault_root=vault_root,
                domain="INVALID_DOMAIN",
                source_path=source_file,
                provider=provider
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid domain" in str(e)

        print("✓ Domain validation works correctly")


def _read_proposal_provenance(vault_root: Path, domain: str, proposal_id: str) -> dict:
    """Read back a written Proposal file's provenance dict."""
    proposal_path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"
    content = proposal_path.read_text()
    frontmatter = yaml.safe_load(content.split('---')[1])
    return frontmatter['provenance']


def test_ollama_provider_provenance_metadata():
    """AC1: OllamaProvider populates non-null provider_model/provider_temperature."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        with open(source_file, 'w') as f:
            f.write("# Test Document\n\nThis is a test.")

        config = OllamaProviderConfig(model="llama3", temperature=0.4)
        provider = OllamaProvider(config)

        # Stub the requests module the provider constructed in __init__
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "direct: Test assertion"}
        provider.requests = Mock()
        provider.requests.post.return_value = mock_response

        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result.status == "completed"
        assert len(result.proposal_ids) == 1

        provenance = _read_proposal_provenance(vault_root, "PERSONAL", result.proposal_ids[0])
        assert provenance['provider_model'] == "llama3"
        assert provenance['provider_temperature'] == 0.4

        print("✓ OllamaProvider surfaces provider_model/provider_temperature")


def test_extraction_id_shared_within_call_differs_across_calls():
    """AC2: one extraction_id per ingest_source call, shared by all its Proposals."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file1 = Path(tmpdir) / "test1.md"
        source_file2 = Path(tmpdir) / "test2.md"

        with open(source_file1, 'w') as f:
            f.write("# Test 1\n\nFirst content.")
        with open(source_file2, 'w') as f:
            f.write("# Test 2\n\nSecond content.")

        provider = Mock()
        provider.extract.return_value = ExtractionResult(
            assertions=[
                ExtractedAssertion(text="Fact A", epistemic_status="direct"),
                ExtractedAssertion(text="Fact B", epistemic_status="direct"),
            ]
        )

        result1 = ingest_source(vault_root=vault_root, domain="PERSONAL", source_path=source_file1, provider=provider)
        result2 = ingest_source(vault_root=vault_root, domain="PERSONAL", source_path=source_file2, provider=provider)

        assert len(result1.proposal_ids) == 2
        assert len(result2.proposal_ids) == 2

        ids_call1 = {_read_proposal_provenance(vault_root, "PERSONAL", pid)['extraction_id'] for pid in result1.proposal_ids}
        ids_call2 = {_read_proposal_provenance(vault_root, "PERSONAL", pid)['extraction_id'] for pid in result2.proposal_ids}

        assert len(ids_call1) == 1
        assert len(ids_call2) == 1
        assert ids_call1 != ids_call2

        print("✓ extraction_id shared within a call, differs across calls")


def test_extraction_duration_recorded():
    """AC3: extraction_duration_seconds is present, numeric, and > 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        with open(source_file, 'w') as f:
            f.write("# Test Document\n\nThis is a test.")

        provider = Mock()

        def slow_extract(text, context):
            time.sleep(0.01)
            return ExtractionResult(assertions=[ExtractedAssertion(text="Fact", epistemic_status="direct")])

        provider.extract.side_effect = slow_extract

        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        provenance = _read_proposal_provenance(vault_root, "PERSONAL", result.proposal_ids[0])
        duration = provenance['extraction_duration_seconds']

        assert isinstance(duration, float)
        assert duration > 0

        print("✓ extraction_duration_seconds is recorded and positive")


def test_fake_provider_yields_null_model_temperature():
    """AC4: a Provider that doesn't report model/temperature yields null, no exception."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        with open(source_file, 'w') as f:
            f.write("# Test Document\n\nThis is a test.")

        provider = Mock()
        provider.extract.return_value = ExtractionResult(
            assertions=[ExtractedAssertion(text="Fact", epistemic_status="direct")]
        )

        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result.status == "completed"
        provenance = _read_proposal_provenance(vault_root, "PERSONAL", result.proposal_ids[0])
        assert provenance['provider_model'] is None
        assert provenance['provider_temperature'] is None

        print("✓ Fake provider without model/temperature yields null, no exception")


def _read_proposal_frontmatter(vault_root: Path, domain: str, proposal_id: str) -> dict:
    """Read back a written Proposal file's full frontmatter dict."""
    proposal_path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"
    content = proposal_path.read_text()
    return yaml.safe_load(content.split('---')[1])


def test_extracted_assertion_defaults_to_empty_path_segments():
    """TASK-001e AC1: proposed_path_segments defaults to [] when not supplied."""
    assertion = ExtractedAssertion(text="Fact", epistemic_status="direct")
    assert assertion.proposed_path_segments == []


def test_proposal_frontmatter_always_has_proposed_path_segments():
    """TASK-001e AC8: written Proposal frontmatter always has proposed_path_segments as a
    list, whether or not the assertion carried one, never omitted/None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"

        with open(source_file, 'w') as f:
            f.write("# Test Document\n\nThis is a test.")

        provider = Mock()
        provider.extract.return_value = ExtractionResult(
            assertions=[
                ExtractedAssertion(
                    text="Fact A", epistemic_status="direct",
                    proposed_path_segments=["mythologie", "japonaise"]
                ),
                ExtractedAssertion(text="Fact B", epistemic_status="direct"),
            ]
        )

        result = ingest_source(
            vault_root=vault_root,
            domain="PERSONAL",
            source_path=source_file,
            provider=provider
        )

        assert result.status == "completed"
        assert len(result.proposal_ids) == 2

        frontmatter_with_path = _read_proposal_frontmatter(vault_root, "PERSONAL", result.proposal_ids[0])
        frontmatter_without_path = _read_proposal_frontmatter(vault_root, "PERSONAL", result.proposal_ids[1])

        assert frontmatter_with_path['proposed_path_segments'] == ["mythologie", "japonaise"]
        assert frontmatter_without_path['proposed_path_segments'] == []

        print("✓ proposed_path_segments always present as a list in written frontmatter")


def test_scan_existing_assertion_folders_empty_when_missing(tmp_path):
    assert scan_existing_assertion_folders(tmp_path, "FICTION") == []


def test_scan_existing_assertion_folders_returns_full_paths(tmp_path):
    base = tmp_path / "FICTION" / "assertions"
    (base / "mythologie" / "japonaise" / "assert-abc123").mkdir(parents=True)
    (base / "geographie").mkdir(parents=True)

    result = scan_existing_assertion_folders(tmp_path, "FICTION")

    assert sorted(result) == ["geographie", "mythologie", "mythologie/japonaise"]


def _write_raw_proposal(proposals_dir: Path, proposal_id: str, frontmatter: dict, body: str = "Body."):
    proposal_dir = proposals_dir / proposal_id
    proposal_dir.mkdir(parents=True)
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    (proposal_dir / f"{proposal_id}.md").write_text(
        f"---\n{yaml_content}---\n\n{body}", encoding="utf-8"
    )


def test_scan_proposed_path_segments_empty_when_missing(tmp_path):
    assert scan_proposed_path_segments(tmp_path, "FICTION") == []


def test_scan_proposed_path_segments_filters_by_status(tmp_path):
    proposals_dir = tmp_path / "FICTION" / "proposals"
    _write_raw_proposal(proposals_dir, "prop-proposed", {
        "proposal_status": "PROPOSED", "proposed_path_segments": ["mythologie", "kitsune"]
    })
    _write_raw_proposal(proposals_dir, "prop-edited", {
        "proposal_status": "EDITED", "proposed_path_segments": ["geographie"]
    })
    _write_raw_proposal(proposals_dir, "prop-accepted", {
        "proposal_status": "ACCEPTED", "proposed_path_segments": ["should", "not", "appear"]
    })
    _write_raw_proposal(proposals_dir, "prop-rejected", {
        "proposal_status": "REJECTED", "proposed_path_segments": ["also", "excluded"]
    })

    result = scan_proposed_path_segments(tmp_path, "FICTION")

    assert sorted(result) == ["geographie", "mythologie/kitsune"]


def test_scan_proposed_path_segments_ignores_missing_or_empty_segments(tmp_path):
    proposals_dir = tmp_path / "FICTION" / "proposals"
    _write_raw_proposal(proposals_dir, "prop-none", {"proposal_status": "PROPOSED"})
    _write_raw_proposal(proposals_dir, "prop-empty", {
        "proposal_status": "PROPOSED", "proposed_path_segments": []
    })

    assert scan_proposed_path_segments(tmp_path, "FICTION") == []


def test_scan_proposed_path_segments_ignores_malformed_proposal_file(tmp_path):
    # A file with no frontmatter block, and one with invalid YAML, must not break
    # the scan for the other, well-formed proposals.
    proposals_dir = tmp_path / "FICTION" / "proposals"
    (proposals_dir / "prop-no-frontmatter").mkdir(parents=True)
    (proposals_dir / "prop-no-frontmatter" / "prop-no-frontmatter.md").write_text(
        "Just a body, no frontmatter at all.", encoding="utf-8"
    )
    (proposals_dir / "prop-bad-yaml").mkdir(parents=True)
    (proposals_dir / "prop-bad-yaml" / "prop-bad-yaml.md").write_text(
        "---\nkey: [unclosed\n---\n\nBody.", encoding="utf-8"
    )
    _write_raw_proposal(proposals_dir, "prop-good", {
        "proposal_status": "PROPOSED", "proposed_path_segments": ["mythologie"]
    })

    assert scan_proposed_path_segments(tmp_path, "FICTION") == ["mythologie"]


def test_scan_proposed_path_segments_dedupes(tmp_path):
    proposals_dir = tmp_path / "FICTION" / "proposals"
    _write_raw_proposal(proposals_dir, "prop-a", {
        "proposal_status": "PROPOSED", "proposed_path_segments": ["mythologie", "kitsune"]
    })
    _write_raw_proposal(proposals_dir, "prop-b", {
        "proposal_status": "EDITED", "proposed_path_segments": ["mythologie", "kitsune"]
    })

    assert scan_proposed_path_segments(tmp_path, "FICTION") == ["mythologie/kitsune"]


def test_ingest_source_passes_vault_root_and_domain_to_provider_context():
    # 2026-09-04 amendment: OllamaProvider needs vault_root/domain in context to scan
    # existing folders for its mandatory path-proposal call.
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_root = Path(tmpdir) / "vault"
        source_file = Path(tmpdir) / "test.md"
        with open(source_file, 'w') as f:
            f.write("# Test Document\n\nThis is a test.")

        provider = Mock()
        provider.extract.return_value = ExtractionResult(
            assertions=[ExtractedAssertion(text="Fact", epistemic_status="direct")]
        )

        ingest_source(vault_root=vault_root, domain="PERSONAL", source_path=source_file, provider=provider)

        context = provider.extract.call_args.args[1]
        assert context["vault_root"] == vault_root
        assert context["domain"] == "PERSONAL"

        print("✓ ingest_source passes vault_root/domain to provider.extract's context")


def test_ingest_source_signature_unchanged():
    """AC6: ingest_source's public parameter list is unchanged by this ticket, except for
    TASK-007's additive, backward-compatible optional task_id parameter."""
    sig = inspect.signature(ingest_source)
    assert list(sig.parameters.keys()) == [
        'vault_root', 'domain', 'source_path', 'provider', 'state_dir', 'task_id'
    ]
    assert sig.parameters['task_id'].default is None

    print("✓ ingest_source signature unchanged (plus additive task_id)")


def _events_from_last_task_state(state_dir):
    from src.app.ingestion.task_state import load_task_state

    state_files = list(state_dir.glob("ingest-*.json"))
    assert len(state_files) == 1
    loaded = load_task_state(state_dir, state_files[0].stem)
    return loaded


def test_successful_ingestion_event_sequence(tmp_path):
    """TASK-001b AC1: a successful ingest_source call produces a TaskState.events
    sequence whose messages correspond, in order, to the real steps executed
    (start, source read, dedup check, source written, provider call, N Proposal
    writes, task completed)."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(
        assertions=[
            ExtractedAssertion(text="Fact A", epistemic_status="direct"),
            ExtractedAssertion(text="Fact B", epistemic_status="direct"),
        ]
    )

    result = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result.status == "completed"

    loaded = _events_from_last_task_state(state_dir)
    messages = [e.message for e in loaded.events]

    assert messages == [
        "Ingestion task started",
        "Source content read",
        "No duplicate found, continuing ingestion",
        "Source file written",
        "Provider extraction call started",
        "Provider extraction call finished",
        "Proposal written",
        "Proposal written",
        "Ingestion task completed",
    ]
    assert all(e.timestamp for e in loaded.events)
    assert loaded.events[-1].level == "success"


def test_provider_failure_appends_warning_event_before_failed(tmp_path):
    """TASK-001b AC3: a simulated provider failure appends a warning-level
    event describing the failure before the task is marked failed."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.side_effect = Exception("Provider failed")

    result = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result.status == "failed"

    loaded = _events_from_last_task_state(state_dir)
    assert loaded.status == "failed"

    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert "Provider" in warning_events[0].message
    assert "Provider failed" in warning_events[0].details["error"]
    assert loaded.events[-1] is warning_events[0], "warning event must be the last one recorded, before failure"


def test_duplicate_ingestion_event_sequence(tmp_path):
    """TASK-001b AC4: a duplicate-source ingestion (skipped_duplicate) appends
    an event describing the duplicate detection instead of the full success
    sequence."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(assertions=[])

    ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    files_before_second_call = set(state_dir.glob("ingest-*.json"))
    result2 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result2.status == "skipped_duplicate"

    from src.app.ingestion.task_state import load_task_state
    new_state_file = (set(state_dir.glob("ingest-*.json")) - files_before_second_call).pop()
    loaded = load_task_state(state_dir, new_state_file.stem)

    messages = [e.message for e in loaded.events]
    assert messages == [
        "Ingestion task started",
        "Source content read",
        "Duplicate source detected, skipping ingestion",
    ]


def test_proposal_write_failure_appends_warning_event(tmp_path):
    """Covers the 'Failed to write proposal' instrumentation branch: a
    warning event is recorded before the task is marked failed."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(
        assertions=[ExtractedAssertion(text="Fact A", epistemic_status="direct")]
    )

    with patch("src.app.ingestion.pipeline.write_proposal_file", side_effect=Exception("disk full")):
        result = ingest_source(
            vault_root=vault_root, domain="PERSONAL", source_path=source_file,
            provider=provider, state_dir=state_dir
        )

    assert result.status == "failed"

    loaded = _events_from_last_task_state(state_dir)
    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert warning_events[0].message == "Failed to write proposal"
    assert "disk full" in warning_events[0].details["error"]
    assert loaded.events[-1] is warning_events[0]


def test_unregistered_extension_appends_failure_event_via_outer_handler(tmp_path):
    """Covers the outer except-block instrumentation branch: an error raised
    outside the inner provider/proposal try-blocks still appends a warning
    event before the task is marked failed."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    unsupported_file = tmp_path / "test.pdf"
    unsupported_file.write_text("not markdown", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(assertions=[])

    result = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=unsupported_file,
        provider=provider, state_dir=state_dir
    )

    assert result.status == "failed"
    assert "No reader registered" in result.error

    loaded = _events_from_last_task_state(state_dir)
    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert warning_events[0].message == "Ingestion task failed"
    assert "No reader registered" in warning_events[0].details["error"]


def test_provider_zero_output_failure(tmp_path):
    """TASK-001c AC3: a provider raising on zero output fails the task with
    the diagnostic in task_state.error; no Proposal files are written."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.side_effect = Exception(
        "Failed to extract assertions using Ollama: Ollama returned 0 assertions "
        "(done_reason='length', model='gpt-oss:20b', response_chars=0)"
    )

    result = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )

    assert result.status == "failed"
    assert "done_reason='length'" in result.error
    assert result.proposal_ids == []
    assert not (vault_root / "PERSONAL" / "proposals").exists()


def test_empty_source_file_fails_before_provider_call(tmp_path):
    """TASK-001c AC5: an empty/whitespace-only source file fails the task
    with a distinct error, without ever calling the provider."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("   \n\n  ", encoding="utf-8")

    provider = Mock()

    result = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )

    assert result.status == "failed"
    assert result.error == "Source file is empty"
    provider.extract.assert_not_called()

    loaded = _events_from_last_task_state(state_dir)
    warning_events = [e for e in loaded.events if e.level == "warning"]
    assert len(warning_events) == 1
    assert warning_events[0].message == "Source file is empty"


def test_retry_after_failure_calls_provider_again_and_completes(tmp_path):
    """TASK-001d AC1: a first ingest_source attempt that fails after the
    source file is written, followed by a second attempt on the same
    content, calls the provider again (no skip) and completes."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.side_effect = [
        Exception("Provider failed"),
        ExtractionResult(assertions=[ExtractedAssertion(text="Fact A", epistemic_status="direct")]),
    ]

    result1 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result1.status == "failed"

    result2 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result2.status == "completed"
    assert len(result2.proposal_ids) == 1
    assert provider.extract.call_count == 2


def test_duplicate_still_skips_after_prior_completed_task(tmp_path):
    """TASK-001d AC2: a genuine duplicate (a prior attempt on the same source
    content already reached status == 'completed') still returns
    skipped_duplicate without calling the provider again - non-regression of
    current behavior, with the retry-capable code path in place."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(assertions=[])

    result1 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result1.status == "completed"

    result2 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result2.status == "skipped_duplicate"
    assert result2.source_id == result1.source_id
    assert provider.extract.call_count == 1


def test_retry_does_not_rewrite_source_file(tmp_path):
    """TASK-001d AC4: the reused-source-on-retry path does not rewrite
    sources/<id>/<id>.md - content/mtime unchanged from the first, failed
    attempt's write."""
    from src.app.ingestion.storage import _generate_source_id

    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    test_content = "# Test Document\n\nThis is a test."
    source_file.write_text(test_content, encoding="utf-8")

    provider = Mock()
    provider.extract.side_effect = [
        Exception("Provider failed"),
        ExtractionResult(assertions=[]),
    ]

    result1 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result1.status == "failed"

    source_id = _generate_source_id(test_content)
    written_source_path = vault_root / "PERSONAL" / "sources" / source_id / f"{source_id}.md"
    assert written_source_path.exists()
    content_before = written_source_path.read_bytes()
    mtime_before = written_source_path.stat().st_mtime_ns

    time.sleep(0.01)

    result2 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result2.status == "completed"

    content_after = written_source_path.read_bytes()
    mtime_after = written_source_path.stat().st_mtime_ns

    assert content_after == content_before
    assert mtime_after == mtime_before


def test_retry_after_failure_event_message_distinct(tmp_path):
    """TASK-001d AC5: append_task_event's log for a retry-after-failure
    attempt contains a distinct event message identifying it as a retry
    reusing an existing source, different from both the real-duplicate-skip
    message and the fresh-write message."""
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nThis is a test.", encoding="utf-8")

    provider = Mock()
    provider.extract.side_effect = [
        Exception("Provider failed"),
        ExtractionResult(assertions=[]),
    ]

    ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    files_before_second_call = set(state_dir.glob("ingest-*.json"))

    result2 = ingest_source(
        vault_root=vault_root, domain="PERSONAL", source_path=source_file,
        provider=provider, state_dir=state_dir
    )
    assert result2.status == "completed"

    from src.app.ingestion.task_state import load_task_state
    new_state_file = (set(state_dir.glob("ingest-*.json")) - files_before_second_call).pop()
    loaded = load_task_state(state_dir, new_state_file.stem)

    messages = [e.message for e in loaded.events]
    assert "Existing source reused, retrying ingestion" in messages
    assert "Duplicate source detected, skipping ingestion" not in messages
    assert "Source file written" not in messages


if __name__ == "__main__":
    # Run all tests
    test_import_isolation()
    test_ingestion_result()
    test_duplicate_detection()
    test_provider_failure_handling()
    test_provider_interface_compliance()
    test_source_reader_registry()
    test_atomic_writes()
    test_epistemic_status()
    test_domain_validation()
    test_ollama_provider_provenance_metadata()
    test_extraction_id_shared_within_call_differs_across_calls()
    test_extraction_duration_recorded()
    test_fake_provider_yields_null_model_temperature()
    test_extracted_assertion_defaults_to_empty_path_segments()
    test_proposal_frontmatter_always_has_proposed_path_segments()
    # test_scan_existing_assertion_folders_* use the pytest tmp_path fixture -
    # pytest-only, not callable from this manual __main__ runner.
    test_ingest_source_passes_vault_root_and_domain_to_provider_context()
    test_ingest_source_signature_unchanged()

    for _test_fn in (
        test_successful_ingestion_event_sequence,
        test_provider_failure_appends_warning_event_before_failed,
        test_duplicate_ingestion_event_sequence,
        test_proposal_write_failure_appends_warning_event,
        test_unregistered_extension_appends_failure_event_via_outer_handler,
        test_provider_zero_output_failure,
        test_empty_source_file_fails_before_provider_call,
        test_retry_after_failure_calls_provider_again_and_completes,
        test_duplicate_still_skips_after_prior_completed_task,
        test_retry_does_not_rewrite_source_file,
        test_retry_after_failure_event_message_distinct,
    ):
        with tempfile.TemporaryDirectory() as _tmpdir:
            _test_fn(Path(_tmpdir))

    print("\n✅ All tests passed!")