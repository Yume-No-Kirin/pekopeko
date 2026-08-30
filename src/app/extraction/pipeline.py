"""
Entity/Event/Relationship extraction pipeline orchestration.

Implements SOURCE -> AI EXTRACTION -> PROPOSAL (specs/domain/knowledge-model.md)
for entities, events, and relationships. Stops at proposal_status: PROPOSED -
review/accept/reject is a separate future ticket.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from . import storage
from .errors import InvalidDomainError
from .providers.base import Provider
from .readers.base import SourceReaderRegistry
from .readers.markdown_reader import MarkdownReader
from .task_state import TaskState, create_task_state, update_task_state

DEFAULT_STATE_DIR = Path.home() / ".pekopeko" / "extraction_state"


class ExtractionPipelineResult:
    """
    Named distinctly from providers.base.ExtractionResult (the raw
    entities/events/relationships a provider returns) to avoid confusion
    with this pipeline-level outcome.
    """

    def __init__(
        self,
        source_id: Optional[str],
        proposal_ids: List[str],
        status: str,
        error: Optional[str] = None,
        skipped_duplicate: bool = False,
    ):
        self.source_id = source_id
        self.proposal_ids = proposal_ids
        self.status = status  # completed, failed, skipped_duplicate
        self.error = error
        self.skipped_duplicate = skipped_duplicate


def _build_reader_registry() -> SourceReaderRegistry:
    registry = SourceReaderRegistry()
    registry.register(".md", MarkdownReader)
    return registry


def extract_source(
    vault_root: Path,
    domain: str,
    source_path: Path,
    provider: Provider,
    state_dir: Path = None,
) -> ExtractionPipelineResult:
    if domain not in storage.VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(storage.VALID_DOMAINS)}")

    if state_dir is None:
        state_dir = DEFAULT_STATE_DIR

    task_state = create_task_state(str(source_path), domain, state_dir)
    update_task_state(task_state, state_dir)

    try:
        task_state.status = "running"
        update_task_state(task_state, state_dir)

        registry = _build_reader_registry()
        content = registry.read_file(source_path)

        source_id = storage._generate_source_id(content)

        if storage.source_exists(vault_root, domain, source_id):
            task_state.source_id = source_id
            task_state.status = "skipped_duplicate"
            task_state.completed_at = datetime.now().isoformat()
            update_task_state(task_state, state_dir)
            return ExtractionPipelineResult(
                source_id=source_id, proposal_ids=[], status="skipped_duplicate", skipped_duplicate=True
            )

        storage.write_source_file(vault_root, domain, content)
        task_state.source_id = source_id
        update_task_state(task_state, state_dir)

        extraction_provider = type(provider).__name__
        try:
            extraction_result = provider.extract(content, {"source_path": str(source_path)})
        except Exception as e:
            task_state.status = "failed"
            task_state.error = str(e)
            task_state.completed_at = datetime.now().isoformat()
            update_task_state(task_state, state_dir)
            return ExtractionPipelineResult(
                source_id=source_id, proposal_ids=[], status="failed", error=task_state.error
            )

        proposal_ids: List[str] = []
        local_id_to_proposal_id = {}

        try:
            for entity in extraction_result.entities:
                proposal_id = storage.write_entity_proposal_file(
                    vault_root, domain, entity, source_id, extraction_provider
                )
                local_id_to_proposal_id[entity.local_id] = proposal_id
                proposal_ids.append(proposal_id)
                task_state.proposal_ids = proposal_ids
                update_task_state(task_state, state_dir)

            for event in extraction_result.events:
                proposal_id = storage.write_event_proposal_file(
                    vault_root, domain, event, source_id, extraction_provider
                )
                local_id_to_proposal_id[event.local_id] = proposal_id
                proposal_ids.append(proposal_id)
                task_state.proposal_ids = proposal_ids
                update_task_state(task_state, state_dir)

            for relationship in extraction_result.relationships:
                resolved_endpoints = [
                    local_id_to_proposal_id.get(endpoint, endpoint)
                    for endpoint in relationship.endpoints
                ]
                proposal_id = storage.write_relationship_proposal_file(
                    vault_root, domain, relationship, resolved_endpoints, source_id, extraction_provider
                )
                proposal_ids.append(proposal_id)
                task_state.proposal_ids = proposal_ids
                update_task_state(task_state, state_dir)
        except Exception as e:
            task_state.status = "failed"
            task_state.error = f"Failed to write proposal: {e}"
            task_state.completed_at = datetime.now().isoformat()
            update_task_state(task_state, state_dir)
            return ExtractionPipelineResult(
                source_id=source_id, proposal_ids=proposal_ids, status="failed", error=task_state.error
            )

        task_state.status = "completed"
        task_state.completed_at = datetime.now().isoformat()
        update_task_state(task_state, state_dir)

        return ExtractionPipelineResult(
            source_id=source_id, proposal_ids=proposal_ids, status="completed"
        )

    except Exception as e:
        task_state.status = "failed"
        task_state.error = str(e)
        task_state.completed_at = datetime.now().isoformat()
        update_task_state(task_state, state_dir)
        return ExtractionPipelineResult(
            source_id=task_state.source_id, proposal_ids=task_state.proposal_ids,
            status="failed", error=task_state.error
        )
