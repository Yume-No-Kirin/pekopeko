"""
Canonical Item Storage Primitive for Knowledge Core

Implements atomic read/write operations for canonical knowledge items with full history tracking.
"""

import os
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import tempfile

# Domain and item type constants
DOMAINS = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}
ITEM_TYPES_PLURAL = {"entities", "assertions", "events", "relationships", "proposals"}
ITEM_TYPES_SINGULAR = {"entity", "assertion", "event", "relationship", "proposal"}

# Required frontmatter fields
REQUIRED_FIELDS = {
    "id", "type", "domain", "lifecycle_status", "epistemic_status",
    "version", "created_at", "valid_from", "valid_until", "provenance"
}

# Valid values for specific fields
VALID_LIFECYCLE_STATUS = {"ACTIVE", "SUPERSEDED", "STALE", "INVALIDATED"}
VALID_EPISTEMIC_STATUS = {"direct", "inferred", "uncertain", "contested"}

class ValidationError(Exception):
    """Raised when canonical item validation fails."""
    pass

def _validate_frontmatter(frontmatter: Dict) -> None:
    """
    Validate that the frontmatter contains all required fields with correct types.

    Args:
        frontmatter (Dict): The frontmatter dictionary to validate

    Raises:
        ValidationError: If any required field is missing or invalid
    """
    # Check required fields exist
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            raise ValidationError(f"Missing required frontmatter field: {field}")

    # Validate field values
    if frontmatter["lifecycle_status"] not in VALID_LIFECYCLE_STATUS:
        raise ValidationError(
            f"Invalid lifecycle_status: {frontmatter['lifecycle_status']}. "
            f"Must be one of {VALID_LIFECYCLE_STATUS}"
        )

    if frontmatter["epistemic_status"] not in VALID_EPISTEMIC_STATUS:
        raise ValidationError(
            f"Invalid epistemic_status: {frontmatter['epistemic_status']}. "
            f"Must be one of {VALID_EPISTEMIC_STATUS}"
        )

    # Validate domain
    if frontmatter["domain"] not in DOMAINS:
        raise ValidationError(
            f"Invalid domain: {frontmatter['domain']}. "
            f"Must be one of {DOMAINS}"
        )

    # Validate type
    if frontmatter["type"] not in ITEM_TYPES_SINGULAR:
        raise ValidationError(
            f"Invalid type: {frontmatter['type']}. "
            f"Must be one of {ITEM_TYPES_SINGULAR}"
        )

def _write_atomic(file_path: str, content: str) -> None:
    """
    Write content to file atomically by writing to a temp file first, then renaming.

    Args:
        file_path (str): Target file path
        content (str): Content to write
    """
    # Create temporary file in the same directory
    dir_path = os.path.dirname(file_path)

    # Use a more Windows-compatible approach - create a unique temp filename
    import uuid
    temp_filename = f"temp_{uuid.uuid4().hex}.tmp"
    temp_file_path = os.path.join(dir_path, temp_filename)

    try:
        with open(temp_file_path, 'w', encoding='utf-8') as tmp_file:
            tmp_file.write(content)
        # Rename temp file to target file (atomic operation)
        os.replace(temp_file_path, file_path)
    except Exception:
        # Clean up temp file if something went wrong
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise

def _parse_frontmatter(md_content: str) -> Tuple[Dict, str]:
    """
    Parse markdown content into frontmatter and body.

    Args:
        md_content (str): Full markdown content

    Returns:
        Tuple[Dict, str]: (frontmatter_dict, body_str)
    """
    if not md_content.startswith('---\n'):
        raise ValidationError("Invalid markdown format: missing opening frontmatter delimiter")

    parts = md_content.split('---\n', 2)
    if len(parts) < 3:
        raise ValidationError("Invalid markdown format: missing closing frontmatter delimiter")

    frontmatter_str = parts[1]
    body = parts[2].lstrip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in frontmatter: {e}")

    return frontmatter, body

def _format_frontmatter(frontmatter: Dict) -> str:
    """
    Format frontmatter dictionary into YAML string.

    Args:
        frontmatter (Dict): Frontmatter dictionary

    Returns:
        str: Formatted YAML string
    """
    return yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True,
                     sort_keys=False, width=float("inf"))

def write_canonical_item(
    vault_root: str,
    domain: str,
    item_type: str,
    item_id: str,
    frontmatter: Dict,
    body: str
) -> None:
    """
    Write or update a canonical knowledge item.

    When updating an existing item, the previous version is moved to history
    with lifecycle_status: SUPERSEDED and a superseded_by pointer.

    Args:
        vault_root (str): Root path of the Obsidian vault
        domain (str): Domain name (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING)
        item_type (str): Singular form of item type (entity, assertion, event, relationship, proposal)
        item_id (str): Unique identifier for this item
        frontmatter (Dict): Dictionary containing all frontmatter fields
        body (str): Markdown body content

    Raises:
        ValidationError: If validation fails or required fields are missing
        Exception: For other filesystem errors
    """

    # Validate inputs
    if domain not in DOMAINS:
        raise ValidationError(f"Invalid domain: {domain}")

    if item_type not in ITEM_TYPES_SINGULAR:
        raise ValidationError(f"Invalid item type: {item_type}")

    # Validate item_id length - must be <= 200 characters to prevent filesystem errors
    if len(item_id) > 200:
        raise ValidationError(f"item_id exceeds maximum length of 200 characters (got {len(item_id)})")

    # Determine plural form for folder structure
    item_type_plural = {
        "entity": "entities",
        "assertion": "assertions",
        "event": "events",
        "relationship": "relationships",
        "proposal": "proposals"
    }[item_type]

    # Validate frontmatter
    _validate_frontmatter(frontmatter)

    # Check that frontmatter values match the parameters passed to the function
    if frontmatter.get("id") != item_id:
        raise ValidationError(f"frontmatter['id'] ({frontmatter.get('id')}) must match item_id ({item_id})")

    if frontmatter.get("domain") != domain:
        raise ValidationError(f"frontmatter['domain'] ({frontmatter.get('domain')}) must match domain ({domain})")

    if frontmatter.get("type") != item_type:
        raise ValidationError(f"frontmatter['type'] ({frontmatter.get('type')}) must match item_type ({item_type})")

    # Set required fields if not present (but we already validated they exist)
    if "id" not in frontmatter:
        frontmatter["id"] = item_id
    if "type" not in frontmatter:
        frontmatter["type"] = item_type
    if "domain" not in frontmatter:
        frontmatter["domain"] = domain

    # Ensure the file path is valid
    item_dir = os.path.join(vault_root, domain, item_type_plural, item_id)
    history_dir = os.path.join(item_dir, "history")

    # Create all necessary directories
    os.makedirs(item_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    # Determine if this is an update or new item
    main_file_path = os.path.join(item_dir, f"{item_id}.md")

    # If there's no existing ACTIVE file, just write the new one directly
    if not os.path.exists(main_file_path):
        frontmatter["lifecycle_status"] = "ACTIVE"
        frontmatter["version"] = 1

        # Set creation timestamp - keep caller-supplied value if present, otherwise default to now
        if "created_at" not in frontmatter:
            created_at = datetime.now().isoformat()
            frontmatter["created_at"] = created_at

        # Create the full markdown content
        md_content = f"---\n{_format_frontmatter(frontmatter)}---\n\n{body.strip()}\n"

        _write_atomic(main_file_path, md_content)
        return

    # This is an update - read the current ACTIVE file
    with open(main_file_path, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # Parse current frontmatter and body
    try:
        current_frontmatter, current_body = _parse_frontmatter(current_content)
    except ValidationError:
        # If we can't parse the existing file, raise an error
        raise ValidationError("Cannot parse existing canonical item - file may be corrupted")

    # Determine new version number
    new_version = current_frontmatter.get("version", 0) + 1

    # Set timestamp for history file
    timestamp = datetime.now().isoformat()
    history_filename = f"{timestamp.replace(':', '-')}--v{current_frontmatter['version']}.md"
    history_file_path = os.path.join(history_dir, history_filename)

    # Prepare history entry with SUPERSEDED status
    history_frontmatter = current_frontmatter.copy()
    history_frontmatter["lifecycle_status"] = "SUPERSEDED"
    history_frontmatter["superseded_by"] = f"v{new_version}"

    # Write the history entry
    history_md_content = f"---\n{_format_frontmatter(history_frontmatter)}---\n\n{current_body.strip()}\n"
    _write_atomic(history_file_path, history_md_content)

    # Prepare new content with updated metadata
    frontmatter["lifecycle_status"] = "ACTIVE"
    frontmatter["version"] = new_version

    # Set creation timestamp - keep caller-supplied value if present, otherwise default to now
    if "created_at" not in frontmatter:
        created_at = datetime.now().isoformat()
        frontmatter["created_at"] = created_at

    # Create the new main file content
    md_content = f"---\n{_format_frontmatter(frontmatter)}---\n\n{body.strip()}\n"

    _write_atomic(main_file_path, md_content)


def read_canonical_item(
    vault_root: str,
    domain: str,
    item_type: str,
    item_id: str
) -> Tuple[Dict, str]:
    """
    Read the current ACTIVE version of a canonical knowledge item.

    Args:
        vault_root (str): Root path of the Obsidian vault
        domain (str): Domain name (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING)
        item_type (str): Singular form of item type (entity, assertion, event, relationship, proposal)
        item_id (str): Unique identifier for this item

    Returns:
        Tuple[Dict, str]: (frontmatter_dict, body_str) of the ACTIVE version

    Raises:
        FileNotFoundError: If no ACTIVE file exists
        ValidationError: If the file is malformed
    """

    if domain not in DOMAINS:
        raise ValidationError(f"Invalid domain: {domain}")

    if item_type not in ITEM_TYPES_SINGULAR:
        raise ValidationError(f"Invalid item type: {item_type}")

    # Determine plural form for folder structure
    item_type_plural = {
        "entity": "entities",
        "assertion": "assertions",
        "event": "events",
        "relationship": "relationships",
        "proposal": "proposals"
    }[item_type]

    # Build file path
    item_dir = os.path.join(vault_root, domain, item_type_plural, item_id)
    main_file_path = os.path.join(item_dir, f"{item_id}.md")

    # Check if file exists
    if not os.path.exists(main_file_path):
        raise FileNotFoundError(f"No active canonical item found at {main_file_path}")

    # Read and parse the file
    with open(main_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        frontmatter, body = _parse_frontmatter(content)
    except ValidationError:
        raise ValidationError("Cannot parse canonical item - file may be corrupted")

    # Validate that this is an ACTIVE version
    if frontmatter.get("lifecycle_status") != "ACTIVE":
        raise ValidationError(f"Item is not in ACTIVE status: {frontmatter.get('lifecycle_status')}")

    return frontmatter, body


def read_item_history(
    vault_root: str,
    domain: str,
    item_type: str,
    item_id: str
) -> List[Dict]:
    """
    Read all SUPERSEDED versions of a canonical knowledge item.

    Args:
        vault_root (str): Root path of the Obsidian vault
        domain (str): Domain name (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING)
        item_type (str): Singular form of item type (entity, assertion, event, relationship, proposal)
        item_id (str): Unique identifier for this item

    Returns:
        List[Dict]: List of dictionaries containing frontmatter and body for each superseded version,
                    ordered from oldest to newest

    Raises:
        ValidationError: If the history directory cannot be accessed
    """

    if domain not in DOMAINS:
        raise ValidationError(f"Invalid domain: {domain}")

    if item_type not in ITEM_TYPES_SINGULAR:
        raise ValidationError(f"Invalid item type: {item_type}")

    # Determine plural form for folder structure
    item_type_plural = {
        "entity": "entities",
        "assertion": "assertions",
        "event": "events",
        "relationship": "relationships",
        "proposal": "proposals"
    }[item_type]

    # Build history directory path
    item_dir = os.path.join(vault_root, domain, item_type_plural, item_id)
    history_dir = os.path.join(item_dir, "history")

    # Check if history directory exists
    if not os.path.exists(history_dir):
        return []

    # Get all history files and sort them by timestamp (oldest first)
    history_files = []
    for filename in os.listdir(history_dir):
        if filename.endswith('.md'):
            history_files.append(filename)

    # Sort by timestamp - we'll use the timestamp in the filename
    history_files.sort()

    # Read each history file
    history_entries = []
    for filename in history_files:
        filepath = os.path.join(history_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            frontmatter, body = _parse_frontmatter(content)
            # Add the full entry to our result
            history_entries.append({
                "frontmatter": frontmatter,
                "body": body
            })
        except ValidationError:
            # Skip malformed history entries but continue processing others
            continue

    return history_entries