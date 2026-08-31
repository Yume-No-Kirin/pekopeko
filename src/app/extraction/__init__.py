"""
Entity/Event/Relationship extraction pipeline: SOURCE -> AI EXTRACTION -> PROPOSAL.
"""
from .pipeline import extract_source, ExtractionPipelineResult
from .providers.base import (
    Provider,
    ExtractionResult,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
)
from .providers.ollama_provider import OllamaProvider, OllamaProviderConfig
from .readers.base import SourceReaderRegistry
from .storage import (
    write_source_file,
    write_entity_proposal_file,
    write_event_proposal_file,
    write_relationship_proposal_file,
)
from .task_state import TaskState, TaskEvent, append_task_event
from .errors import ExtractionError, InvalidDomainError, ValidationError

__all__ = [
    'extract_source', 'ExtractionPipelineResult', 'Provider', 'ExtractionResult',
    'ExtractedEntity', 'ExtractedEvent', 'ExtractedRelationship',
    'OllamaProvider', 'OllamaProviderConfig', 'SourceReaderRegistry',
    'write_source_file', 'write_entity_proposal_file', 'write_event_proposal_file',
    'write_relationship_proposal_file', 'TaskState', 'TaskEvent', 'append_task_event',
    'ExtractionError', 'InvalidDomainError', 'ValidationError',
]
