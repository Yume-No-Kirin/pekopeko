"""
Main ingestion pipeline for processing source files.
"""
import os
import time
import uuid
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from ..config import load_config
from .providers.base import Provider, ExtractionResult
from .readers.base import SourceReaderRegistry
from .readers.markdown_reader import MarkdownReader
from .storage import write_source_file, write_proposal_file, _generate_source_id
from .task_state import TaskState, create_task_state, update_task_state, append_task_event


class IngestionResult:
    """Represents the result of an ingestion operation."""

    def __init__(
        self,
        source_id: Optional[str] = None,
        proposal_ids: Optional[List[str]] = None,
        status: str = "completed",
        error: Optional[str] = None,
        skipped_duplicate: bool = False
    ):
        self.source_id = source_id
        self.proposal_ids = proposal_ids or []
        self.status = status  # completed, failed, skipped_duplicate
        self.error = error
        self.skipped_duplicate = skipped_duplicate


def ingest_source(
    vault_root: Path,
    domain: str,
    source_path: Path,
    provider: Provider,
    state_dir: Path = None,
    task_id: Optional[str] = None
) -> IngestionResult:
    """
    Ingest a single source file and extract assertions.

    Args:
        vault_root: Root directory of the vault
        domain: Domain name (PERSONAL, FICTION, etc.)
        source_path: Path to the source file
        provider: LLM provider to use for extraction
        state_dir: Directory for task state storage (optional)
        task_id: Pre-minted task id to use verbatim (optional)

    Returns:
        IngestionResult with details of the operation
    """
    # Validate domain - using ADI-004 compliant domains
    valid_domains = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}
    if domain not in valid_domains:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of {valid_domains}")

    # Create task state if not provided
    if state_dir is None:
        state_dir = load_config().task_state.dir / "ingestion"

    task_state = create_task_state(str(source_path), domain, state_dir, task_id=task_id)
    update_task_state(task_state, state_dir)
    append_task_event(task_state, state_dir, "info", "Ingestion task started",
                       {"source_path": str(source_path), "domain": domain})

    try:
        # Update task state to running
        task_state.status = "running"
        update_task_state(task_state, state_dir)

        # Initialize result
        result = IngestionResult()

        # Register markdown reader
        registry = SourceReaderRegistry()
        registry.register(".md", MarkdownReader)

        # Read source content
        content = registry.read_file(source_path)
        append_task_event(task_state, state_dir, "info", "Source content read",
                           {"source_path": str(source_path)})

        # Check for duplicate ingestion
        source_id = _generate_source_id(content)
        existing_source_path = vault_root / domain / "sources" / source_id / f"{source_id}.md"

        if existing_source_path.exists():
            # Skip duplicate ingestion
            append_task_event(task_state, state_dir, "info", "Duplicate source detected, skipping ingestion",
                               {"source_id": source_id})
            task_state.status = "skipped_duplicate"
            task_state.source_id = source_id
            update_task_state(task_state, state_dir)
            result.source_id = source_id
            result.skipped_duplicate = True
            result.status = "skipped_duplicate"
            return result

        append_task_event(task_state, state_dir, "info", "No duplicate found, continuing ingestion",
                           {"source_id": source_id})

        # Write source file
        source_id = write_source_file(vault_root, domain, content, source_path.name)
        task_state.source_id = source_id
        update_task_state(task_state, state_dir)
        append_task_event(task_state, state_dir, "info", "Source file written",
                           {"source_id": source_id})

        # Extract assertions using the provider
        extraction_id = f"extract-{uuid.uuid4()}"
        extraction_start = time.monotonic()
        append_task_event(task_state, state_dir, "info", "Provider extraction call started",
                           {"extraction_id": extraction_id})
        try:
            extraction_result: ExtractionResult = provider.extract(content, {"source_path": str(source_path)})
        except Exception as e:
            # Update task state with error and return
            append_task_event(task_state, state_dir, "warning", "Provider extraction call failed",
                               {"extraction_id": extraction_id, "error": str(e)})
            task_state.status = "failed"
            task_state.error = str(e)
            update_task_state(task_state, state_dir)
            result.status = "failed"
            result.error = str(e)
            return result
        extraction_duration_seconds = time.monotonic() - extraction_start
        append_task_event(task_state, state_dir, "success", "Provider extraction call finished",
                           {"extraction_id": extraction_id,
                            "duration_seconds": extraction_duration_seconds,
                            "assertions_count": len(extraction_result.assertions)})

        # Process each extracted assertion
        proposal_ids = []
        for assertion in extraction_result.assertions:
            try:
                proposal_id = write_proposal_file(
                    vault_root, domain, assertion, source_id, type(provider).__name__,
                    provider_model=extraction_result.model,
                    provider_temperature=extraction_result.temperature,
                    extraction_id=extraction_id,
                    extraction_duration_seconds=extraction_duration_seconds
                )
                proposal_ids.append(proposal_id)
                task_state.proposal_ids.append(proposal_id)
                append_task_event(task_state, state_dir, "info", "Proposal written",
                                   {"proposal_id": proposal_id})
            except Exception as e:
                # If we fail to write a single proposal, continue with others
                # but mark the overall task as failed
                append_task_event(task_state, state_dir, "warning", "Failed to write proposal",
                                   {"error": str(e)})
                task_state.status = "failed"
                task_state.error = f"Failed to write proposal: {str(e)}"
                update_task_state(task_state, state_dir)
                result.status = "failed"
                result.error = str(e)
                return result

        # Update task state with completion
        task_state.status = "completed"
        task_state.completed_at = datetime.now().isoformat()
        task_state.proposal_ids = proposal_ids
        update_task_state(task_state, state_dir)
        append_task_event(task_state, state_dir, "success", "Ingestion task completed",
                           {"proposal_count": len(proposal_ids)})

        # Return successful result
        result.source_id = source_id
        result.proposal_ids = proposal_ids
        result.status = "completed"

        return result

    except Exception as e:
        # Handle any other errors
        append_task_event(task_state, state_dir, "warning", "Ingestion task failed",
                           {"error": str(e)})
        task_state.status = "failed"
        task_state.error = str(e)
        update_task_state(task_state, state_dir)
        result.status = "failed"
        result.error = str(e)
        return result


# For backward compatibility - same function name but with different parameter order
def process_source(
    source_path: Path,
    domain: str,
    vault_root: Path,
    provider: Provider,
    state_dir: Path = None
) -> IngestionResult:
    """
    Process a source file (backward compatibility alias).

    Args:
        source_path: Path to the source file
        domain: Domain name (PERSONAL, FICTION, etc.)
        vault_root: Root directory of the vault
        provider: LLM provider to use for extraction
        state_dir: Directory for task state storage (optional)

    Returns:
        IngestionResult with details of the operation
    """
    return ingest_source(vault_root, domain, source_path, provider, state_dir)