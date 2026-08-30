"""
Base interfaces for extraction LLM providers (ADI-008).

Pipeline code depends only on these types - never on a concrete SDK/HTTP
client. Independent of app/ingestion/providers/ - reimplemented rather than
imported, per this ticket's independence requirement.
"""
from dataclasses import dataclass, field
from typing import Optional, Protocol

# Single source of truth for the epistemic_status vocabulary - storage.py
# and providers/ollama_provider.py both import this rather than redefining
# it, so the two validation points can never silently drift apart.
VALID_EPISTEMIC_STATUSES: frozenset[str] = frozenset({"direct", "inferred", "uncertain", "contested"})


@dataclass
class ExtractedEntity:
    """
    local_id is a transient identifier scoped to a single extraction call,
    assigned by the provider so that a co-extracted relationship can refer
    to this entity before it has a real proposal_id (only minted at write
    time). It is never persisted as-is.
    """
    local_id: str
    entity_type: str  # free text, e.g. person|place|organization|object|other
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"


@dataclass
class ExtractedEvent:
    local_id: str
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None


@dataclass
class ExtractedRelationship:
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"
    relationship_type: str
    # Each entry is either a co-extracted entity/event's local_id (resolved
    # to a real proposal_id by the pipeline before writing) or an existing
    # canonical item's stable id, passed through unchanged.
    endpoints: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    entities: list[ExtractedEntity] = field(default_factory=list)
    events: list[ExtractedEvent] = field(default_factory=list)
    relationships: list[ExtractedRelationship] = field(default_factory=list)


class Provider(Protocol):
    def extract(self, text: str, context: dict) -> ExtractionResult: ...
