"""
Base interfaces for LLM providers used in ingestion.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ExtractedAssertion:
    """Represents a single extracted assertion from source content."""
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"


@dataclass
class ExtractionResult:
    """Result of an extraction operation."""
    assertions: list[ExtractedAssertion]


class Provider(Protocol):
    """Interface for LLM providers used in ingestion."""

    def extract(self, text: str, context: dict) -> ExtractionResult: ...