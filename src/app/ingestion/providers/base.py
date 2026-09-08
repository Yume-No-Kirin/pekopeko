"""
Base interfaces for LLM providers used in ingestion.
"""
from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass
class ExtractedAssertion:
    """Represents a single extracted assertion from source content."""
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"
    proposed_path_segments: list[str] = field(default_factory=list)
    # Distinct from proposed_path_segments (ADI-016/TASK-014b) - a single,
    # stable, cross-type identifier resolved once per source note, not per
    # assertion. Optional[str], never forced non-null.
    context: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of an extraction operation."""
    assertions: list[ExtractedAssertion]
    model: Optional[str] = None
    temperature: Optional[float] = None


class Provider(Protocol):
    """Interface for LLM providers used in ingestion."""

    def extract(self, text: str, context: dict) -> ExtractionResult: ...