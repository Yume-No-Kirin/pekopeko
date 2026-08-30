"""
Extensibility tests: second reader (AC5), second provider (AC6).
"""
from pathlib import Path

from _helpers import read_frontmatter

from src.app.extraction import extract_source, ExtractionResult, ExtractedEntity
from src.app.extraction.readers.base import SourceReader, SourceReaderRegistry


class MockTextReader(SourceReader):
    """A second reader, registered only in this test - no pipeline.py change needed."""

    def read(self, path: Path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def test_second_reader_extensibility(tmp_path):
    source_file = tmp_path / "test.txt"
    content = "Plain text source content."
    source_file.write_text(content, encoding="utf-8")

    registry = SourceReaderRegistry()
    registry.register(".txt", MockTextReader)

    read_back = registry.read_file(source_file)
    assert read_back == content


def test_second_provider_extensibility(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test\n\nSome content.", encoding="utf-8")
    vault_root = tmp_path / "vault"

    class MockProvider:
        """A second provider - a plain class structurally satisfying Provider."""

        def extract(self, text: str, context: dict) -> ExtractionResult:
            return ExtractionResult(
                entities=[
                    ExtractedEntity(local_id="e1", entity_type="object", text="Test entity", epistemic_status="direct"),
                ],
            )

    result = extract_source(vault_root, "PERSONAL", source_file, MockProvider(), state_dir=tmp_path / "state")

    assert result.status == "completed"
    assert len(result.proposal_ids) == 1
    fm, _ = read_frontmatter(
        vault_root / "PERSONAL" / "proposals" / result.proposal_ids[0] / f"{result.proposal_ids[0]}.md"
    )
    assert fm["provenance"]["extraction_provider"] == "MockProvider"
