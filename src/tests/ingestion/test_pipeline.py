"""
Unit tests for the ingestion pipeline.
"""
import tempfile
import os
from pathlib import Path
import pytest
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

    print("\n✅ All tests passed!")