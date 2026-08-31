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
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False, suffix='.tmp') as tmp_file:
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