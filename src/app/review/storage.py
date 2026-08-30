"""
Filesystem primitives for the proposal review workflow: atomic writes,
path layout, id generation, and frontmatter field validation.

review/ is independent of ingestion/'s code - the atomic-write pattern is
reimplemented here rather than imported, per TASK-002's independence
requirement (only the on-disk file/frontmatter contract is shared).
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .errors import (
    InvalidDomainError,
    ProposalNotFoundError,
    SourceNotFoundError,
    ValidationError,
)
from .frontmatter import parse_frontmatter, serialize_frontmatter

VALID_DOMAINS = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}

REQUIRED_PROPOSAL_FIELDS = [
    "id", "type", "domain", "proposal_status", "proposed_item_type",
    "epistemic_status", "created_at", "valid_from", "valid_until", "provenance",
]
REQUIRED_ASSERTION_FIELDS = [
    "id", "type", "domain", "epistemic_status", "lifecycle_status",
    "valid_from", "valid_until", "created_at", "provenance",
]
REQUIRED_ASSERTION_PROVENANCE_FIELDS = [
    "source_id", "extraction_provider", "proposal_id", "reviewed_by", "reviewed_at",
]


def _validate_domain(domain: str) -> None:
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")


def _validate_frontmatter(frontmatter: dict[str, Any], required_fields: list[str]) -> None:
    missing_fields = [field for field in required_fields if field not in frontmatter]
    if missing_fields:
        raise ValidationError(f"Missing required frontmatter fields: {missing_fields}")


def _generate_assertion_id() -> str:
    return f"assert-{uuid.uuid4()}"


def proposal_path(vault_root: Path, domain: str, proposal_id: str) -> Path:
    return vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"


def assertion_path(vault_root: Path, domain: str, assertion_id: str) -> Path:
    return vault_root / domain / "assertions" / assertion_id / f"{assertion_id}.md"


def source_path(vault_root: Path, domain: str, source_id: str) -> Path:
    return vault_root / domain / "sources" / source_id / f"{source_id}.md"


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


def read_proposal_file(vault_root: Path, domain: str, proposal_id: str) -> tuple[dict[str, Any], str]:
    path = proposal_path(vault_root, domain, proposal_id)
    if not path.exists():
        raise ProposalNotFoundError(f"No proposal '{proposal_id}' found in domain '{domain}'")
    raw_content = path.read_text(encoding="utf-8")
    return parse_frontmatter(raw_content)


def read_source_file(vault_root: Path, domain: str, source_id: str) -> tuple[dict[str, Any], str]:
    path = source_path(vault_root, domain, source_id)
    if not path.exists():
        raise SourceNotFoundError(f"No source '{source_id}' found in domain '{domain}'")
    raw_content = path.read_text(encoding="utf-8")
    return parse_frontmatter(raw_content)


def list_proposal_ids(vault_root: Path, domain: str) -> list[str]:
    proposals_dir = vault_root / domain / "proposals"
    if not proposals_dir.exists():
        return []
    return sorted(
        item_dir.name
        for item_dir in proposals_dir.iterdir()
        if item_dir.is_dir() and (item_dir / f"{item_dir.name}.md").exists()
    )


def write_assertion_file(vault_root: Path, domain: str, frontmatter: dict[str, Any], body: str) -> Path:
    _validate_frontmatter(frontmatter, REQUIRED_ASSERTION_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_ASSERTION_PROVENANCE_FIELDS)

    path = assertion_path(vault_root, domain, frontmatter["id"])
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def write_proposal_file_in_place(
    vault_root: Path, domain: str, proposal_id: str, frontmatter: dict[str, Any], body: str
) -> Path:
    path = proposal_path(vault_root, domain, proposal_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path
