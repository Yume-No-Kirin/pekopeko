"""
Filesystem primitives for the extraction pipeline: atomic writes, path
layout, id generation, and frontmatter field validation.

Independent of app/ingestion/ and app/review/'s code - the atomic-write
pattern is reimplemented here (with the os.replace failure cleanup that
app/review/storage.py added after finding an orphaned-.tmp bug in
app/ingestion/storage.py during TASK-002's verification), per this
ticket's independence requirement. Only the on-disk file/frontmatter
contract defined by TASK-003's own "File layout (exact contract)" section
is shared/binding.
"""
import hashlib
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .errors import InvalidDomainError, ValidationError
from .frontmatter import serialize_frontmatter
from .providers.base import (
    VALID_EPISTEMIC_STATUSES,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
)

VALID_DOMAINS = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}

REQUIRED_SOURCE_FIELDS = [
    "item_type", "domain", "source_id", "created_at",
    "source_path", "source_format", "content",
]
REQUIRED_PROPOSAL_FIELDS = [
    "id", "type", "item_type", "domain", "created_at", "proposal_status", "provenance",
    "proposed_item_type", "epistemic_status", "valid_from", "valid_until",
]
REQUIRED_PROPOSAL_PROVENANCE_FIELDS = ["source_id", "extraction_provider"]
REQUIRED_ENTITY_FIELDS = ["entity_type"]
REQUIRED_EVENT_FIELDS = ["starts_at", "ends_at"]
REQUIRED_RELATIONSHIP_FIELDS = ["relationship_type", "endpoints"]


def _validate_domain(domain: str) -> None:
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")


def _validate_frontmatter(frontmatter: dict[str, Any], required_fields: list[str]) -> None:
    missing_fields = [field for field in required_fields if field not in frontmatter]
    if missing_fields:
        raise ValidationError(f"Missing required frontmatter fields: {missing_fields}")


def _validate_epistemic_status(status: str) -> None:
    if status not in VALID_EPISTEMIC_STATUSES:
        raise ValidationError(
            f"Invalid epistemic_status '{status}'. Must be one of {sorted(VALID_EPISTEMIC_STATUSES)}"
        )


def _validate_endpoints(endpoints: list[str]) -> None:
    if not endpoints or len(endpoints) < 2:
        raise ValidationError(
            f"Relationship endpoints must contain at least 2 identifiers, got {len(endpoints) if endpoints else 0}"
        )


def _generate_source_id(content: str) -> str:
    return f"src-{hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]}"


def _generate_proposal_id() -> str:
    return f"prop-{uuid.uuid4()}"


def source_file_path(vault_root: Path, domain: str, source_id: str) -> Path:
    return vault_root / domain / "sources" / source_id / f"{source_id}.md"


def proposal_file_path(vault_root: Path, domain: str, proposal_id: str) -> Path:
    return vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"


def source_exists(vault_root: Path, domain: str, source_id: str) -> bool:
    return source_file_path(vault_root, domain, source_id).exists()


def _write_atomic_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, delete=False, suffix=".tmp", encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = tmp_file.name

    try:
        os.replace(tmp_path, path)
    except OSError:
        os.remove(tmp_path)
        raise


def write_source_file(vault_root: Path, domain: str, content: str) -> str:
    """
    Write the Source file, per TASK-003's exact frontmatter contract.
    Returns the generated source_id.
    """
    _validate_domain(domain)

    source_id = _generate_source_id(content)
    now = datetime.now().isoformat()
    relative_path = f"{domain}/sources/{source_id}/{source_id}.md"

    frontmatter = {
        "item_type": "source",
        "domain": domain,
        "source_id": source_id,
        "created_at": now,
        "source_path": relative_path,
        "source_format": "markdown",
        "content": content,
    }
    _validate_frontmatter(frontmatter, REQUIRED_SOURCE_FIELDS)

    path = source_file_path(vault_root, domain, source_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, content))
    return source_id


def _base_proposal_frontmatter(
    proposal_id: str, domain: str, source_id: str, extraction_provider: str,
    proposed_item_type: str, epistemic_status: str,
) -> dict[str, Any]:
    _validate_epistemic_status(epistemic_status)
    now = datetime.now().isoformat()
    return {
        "id": proposal_id,
        "type": "proposal",
        "item_type": "proposal",
        "domain": domain,
        "created_at": now,
        "proposal_status": "PROPOSED",
        "provenance": {
            "source_id": source_id,
            "extraction_provider": extraction_provider,
        },
        "proposed_item_type": proposed_item_type,
        "epistemic_status": epistemic_status,
        "valid_from": now,
        "valid_until": None,
    }


def write_entity_proposal_file(
    vault_root: Path, domain: str, entity: ExtractedEntity, source_id: str, extraction_provider: str
) -> str:
    proposal_id = _generate_proposal_id()
    frontmatter = _base_proposal_frontmatter(
        proposal_id, domain, source_id, extraction_provider, "entity", entity.epistemic_status
    )
    frontmatter["entity_type"] = entity.entity_type

    _validate_frontmatter(frontmatter, REQUIRED_PROPOSAL_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_PROPOSAL_PROVENANCE_FIELDS)
    _validate_frontmatter(frontmatter, REQUIRED_ENTITY_FIELDS)

    path = proposal_file_path(vault_root, domain, proposal_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, entity.text))
    return proposal_id


def write_event_proposal_file(
    vault_root: Path, domain: str, event: ExtractedEvent, source_id: str, extraction_provider: str
) -> str:
    proposal_id = _generate_proposal_id()
    frontmatter = _base_proposal_frontmatter(
        proposal_id, domain, source_id, extraction_provider, "event", event.epistemic_status
    )
    frontmatter["starts_at"] = event.starts_at
    frontmatter["ends_at"] = event.ends_at

    _validate_frontmatter(frontmatter, REQUIRED_PROPOSAL_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_PROPOSAL_PROVENANCE_FIELDS)
    _validate_frontmatter(frontmatter, REQUIRED_EVENT_FIELDS)

    path = proposal_file_path(vault_root, domain, proposal_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, event.text))
    return proposal_id


def write_relationship_proposal_file(
    vault_root: Path, domain: str, relationship: ExtractedRelationship,
    resolved_endpoints: list[str], source_id: str, extraction_provider: str
) -> str:
    _validate_endpoints(resolved_endpoints)

    proposal_id = _generate_proposal_id()
    frontmatter = _base_proposal_frontmatter(
        proposal_id, domain, source_id, extraction_provider, "relationship", relationship.epistemic_status
    )
    frontmatter["relationship_type"] = relationship.relationship_type
    frontmatter["endpoints"] = resolved_endpoints

    _validate_frontmatter(frontmatter, REQUIRED_PROPOSAL_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_PROPOSAL_PROVENANCE_FIELDS)
    _validate_frontmatter(frontmatter, REQUIRED_RELATIONSHIP_FIELDS)

    path = proposal_file_path(vault_root, domain, proposal_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, relationship.text))
    return proposal_id
