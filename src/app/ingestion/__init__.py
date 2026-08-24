"""
Ingestion module for Pekopeko - data ingestion pipeline.
"""
from .pipeline import ingest_source, process_source, IngestionResult
from .providers.base import Provider, ExtractionResult, ExtractedAssertion
from .providers.ollama_provider import OllamaProvider, OllamaProviderConfig
from .readers.base import SourceReaderRegistry
from .storage import write_source_file, write_proposal_file
from .task_state import TaskState

# Export the main classes and functions
__all__ = [
    'ingest_source',
    'process_source',
    'IngestionResult',
    'Provider',
    'ExtractionResult',
    'ExtractedAssertion',
    'OllamaProvider',
    'OllamaProviderConfig',
    'SourceReaderRegistry',
    'write_source_file',
    'write_proposal_file',
    'TaskState'
]