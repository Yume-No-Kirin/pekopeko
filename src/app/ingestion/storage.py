"""
Storage utilities for ingestion pipeline with atomic writes.
"""
import os
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import yaml
from .providers.base import ExtractedAssertion


def _write_atomic_file(path: Path, content: str):
    """
    Write content to a file atomically.

    Args:
        path: Target file path
        content: Content to write
    """
    # Create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file in the same directory
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, suffix='.tmp', encoding='utf-8') as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
        tmp_path = tmp_file.name

    # Atomically replace the original file
    os.replace(tmp_path, path)


def _generate_source_id(content: str) -> str:
    """
    Generate a deterministic source ID from content.

    Args:
        content: Source content

    Returns:
        Source ID in format 'src-<sha256_hash>'
    """
    content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    return f"src-{content_hash[:16]}"


def _generate_proposal_id() -> str:
    """
    Generate a unique proposal ID.

    Returns:
        Proposal ID in format 'prop-<uuid4>'
    """
    import uuid
    return f"prop-{uuid.uuid4()}"


def _validate_frontmatter(frontmatter: Dict[str, Any], required_fields: list[str]):
    """
    Validate that all required frontmatter fields are present.

    Args:
        frontmatter: The frontmatter dictionary to validate
        required_fields: List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in frontmatter]
    if missing_fields:
        raise ValueError(f"Missing required frontmatter fields: {missing_fields}")


def scan_existing_assertion_folders(vault_root: Path, domain: str) -> list[str]:
    """Full existing folder paths already used under <domain>/assertions/ (canonical,
    accepted items only) - context for a provider proposing a new, consistent path.
    Independent reimplementation of review/storage.py's scan_organization_folders
    (module-independence discipline, TASK-002) - returns full "/"-joined paths rather
    than depth-grouped segment names, since that's what a path-proposal prompt needs.
    """
    assertions_dir = vault_root / domain / "assertions"
    if not assertions_dir.exists():
        return []
    paths: list[str] = []

    def _walk(directory: Path, prefix: list[str]) -> None:
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir() or entry.name.startswith("assert-"):
                continue
            new_prefix = prefix + [entry.name]
            paths.append("/".join(new_prefix))
            _walk(entry, new_prefix)

    _walk(assertions_dir, [])
    return paths


def _read_frontmatter(path: Path) -> Dict[str, Any]:
    """Best-effort YAML frontmatter read for a Proposal file - returns {} for a file
    with no frontmatter block, never raises on a malformed one (a single bad Proposal
    file must not break a folder-path scan, same posture already established for
    review/'s list_proposals)."""
    content = path.read_text(encoding='utf-8')
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def scan_proposed_path_segments(vault_root: Path, domain: str) -> list[str]:
    """Full path strings already proposed by not-yet-accepted Proposals
    (proposal_status PROPOSED or EDITED) under <domain>/proposals/ - context so a
    provider's new path proposal reuses the same folder a previously-ingested, still
    unreviewed note already suggested, rather than inventing a new spelling for the
    same concept (ADI-015, amends ADI-014).
    """
    proposals_dir = vault_root / domain / "proposals"
    if not proposals_dir.exists():
        return []
    paths: set[str] = set()
    for proposal_file in proposals_dir.glob("*/*.md"):
        try:
            frontmatter = _read_frontmatter(proposal_file)
        except (OSError, yaml.YAMLError):
            continue
        if frontmatter.get('proposal_status') not in ('PROPOSED', 'EDITED'):
            continue
        segments = frontmatter.get('proposed_path_segments')
        if segments:
            paths.add('/'.join(segments))
    return sorted(paths)


def write_source_file(
    vault_root: Path,
    domain: str,
    content: str,
    original_filename: str
) -> str:
    """
    Write a source file atomically.

    Args:
        vault_root: Root directory of the vault
        domain: Domain name (PERSONAL, FICTION, etc.)
        content: Source content
        original_filename: Original filename

    Returns:
        The source ID that was generated
    """
    # Generate source ID from content
    source_id = _generate_source_id(content)

    # Create file path
    source_path = vault_root / domain / "sources" / source_id / f"{source_id}.md"

    # Prepare frontmatter
    current_time = datetime.now()
    frontmatter = {
        'id': source_id,
        'type': 'source',
        'domain': domain,
        'source_format': 'markdown',
        'original_filename': original_filename,
        'content_hash': hashlib.sha256(content.encode('utf-8')).hexdigest(),
        'ingested_at': current_time.isoformat(),
        'lifecycle_status': 'ACTIVE'
    }

    # Convert frontmatter to YAML
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

    # Create the markdown content with frontmatter
    markdown_content = f"---\n{yaml_content}---\n\n{content}"

    # Write atomically
    _write_atomic_file(source_path, markdown_content)

    return source_id


def write_proposal_file(
    vault_root: Path,
    domain: str,
    assertion: ExtractedAssertion,
    source_id: str,
    extraction_provider: str,
    provider_model: Optional[str] = None,
    provider_temperature: Optional[float] = None,
    extraction_id: Optional[str] = None,
    extraction_duration_seconds: Optional[float] = None
) -> str:
    """
    Write a proposal file atomically.

    Args:
        vault_root: Root directory of the vault
        domain: Domain name (PERSONAL, FICTION, etc.)
        assertion: The extracted assertion
        source_id: ID of the source file this assertion came from
        extraction_provider: Name of the provider that extracted this assertion
        provider_model: Model reported by the provider, if any
        provider_temperature: Temperature reported by the provider, if any
        extraction_id: Pipeline-minted ID shared by all Proposals from the same
            ingest_source call, if any
        extraction_duration_seconds: Wall-clock duration of the provider.extract()
            call, if any

    Returns:
        The proposal ID that was generated
    """
    # Generate proposal ID
    proposal_id = _generate_proposal_id()

    # Create file path
    proposal_path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"

    # Prepare frontmatter
    current_time = datetime.now()
    frontmatter = {
        'id': proposal_id,
        'type': 'proposal',
        'domain': domain,
        'proposal_status': 'PROPOSED',
        'proposed_item_type': 'assertion',
        'epistemic_status': assertion.epistemic_status,
        'proposed_path_segments': assertion.proposed_path_segments,
        'created_at': current_time.isoformat(),
        'valid_from': current_time.isoformat(),
        'valid_until': None,
        'provenance': {
            'source_id': source_id,
            'extraction_provider': extraction_provider,
            'provider_model': provider_model,
            'provider_temperature': provider_temperature,
            'extraction_id': extraction_id,
            'extraction_duration_seconds': extraction_duration_seconds
        }
    }

    # Validate that epistemic_status is one of the required values
    valid_statuses = ["direct", "inferred", "uncertain", "contested"]
    if assertion.epistemic_status not in valid_statuses:
        raise ValueError(f"Invalid epistemic_status '{assertion.epistemic_status}'. Must be one of {valid_statuses}")

    # Validate frontmatter (ensure epistemic_status is present)
    _validate_frontmatter(frontmatter, ['id', 'type', 'domain', 'proposal_status', 'proposed_item_type',
                                       'epistemic_status', 'created_at', 'provenance'])

    # Convert frontmatter to YAML
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

    # Create the markdown content with frontmatter
    markdown_content = f"---\n{yaml_content}---\n\n{assertion.text}"

    # Write atomically
    _write_atomic_file(proposal_path, markdown_content)

    return proposal_id