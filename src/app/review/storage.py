"""
Filesystem primitives for the proposal review workflow: atomic writes,
path layout, id generation, and frontmatter field validation.

review/ is independent of ingestion/'s code - the atomic-write pattern is
reimplemented here rather than imported, per TASK-002's independence
requirement (only the on-disk file/frontmatter contract is shared).
"""
import contextlib
import os
import re
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from .errors import (
    InvalidDomainError,
    ProposalNotFoundError,
    SourceNotFoundError,
    UneditableFieldError,
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
REQUIRED_ENTITY_FIELDS = [
    "id", "type", "domain", "entity_type", "epistemic_status", "lifecycle_status",
    "valid_from", "valid_until", "created_at", "provenance",
]
REQUIRED_EVENT_FIELDS = [
    "id", "type", "domain", "starts_at", "ends_at", "epistemic_status", "lifecycle_status",
    "valid_from", "valid_until", "created_at", "provenance",
]
REQUIRED_RELATIONSHIP_FIELDS = [
    "id", "type", "domain", "relationship_type", "endpoints", "epistemic_status",
    "lifecycle_status", "valid_from", "valid_until", "created_at", "provenance",
]
# Provenance requirement is identical across all four canonical item types
# (assertion/entity/event/relationship) - the "ASSERTION" name predates
# entity/event/relationship support (TASK-005) but is reused as-is rather
# than renamed, to avoid unrelated churn.
REQUIRED_ASSERTION_PROVENANCE_FIELDS = [
    "source_id", "extraction_provider", "proposal_id", "reviewed_by", "reviewed_at",
]

# proposed_path_segments is common to all four types (TASK-005a, ADI-012 adoption
# by entity/event/relationship) - unlike TASK-014's original assertion-only scoping,
# there is no longer a type-specific reason to keep it out of the common set.
# context is cross-type by design from the start (ADI-016/TASK-014a), unlike
# proposed_path_segments' own type-scoped history.
_COMMON_EDITABLE_FIELDS = {
    "body", "epistemic_status", "valid_from", "valid_until", "proposed_path_segments", "context"
}

EDITABLE_FIELDS_BY_TYPE = {
    "assertion": _COMMON_EDITABLE_FIELDS,
    "entity": _COMMON_EDITABLE_FIELDS | {"entity_type"},
    "event": _COMMON_EDITABLE_FIELDS | {"starts_at", "ends_at"},
    "relationship": _COMMON_EDITABLE_FIELDS | {"relationship_type", "endpoints"},
}

_HISTORY_FILENAME_VERSION_RE = re.compile(r"--v(\d+)\.md$")

_EDIT_LOCK_TIMEOUT_SECONDS = 10
_EDIT_LOCK_STALE_SECONDS = 30
_EDIT_LOCK_POLL_SECONDS = 0.05


def _validate_domain(domain: str) -> None:
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")


def _validate_frontmatter(frontmatter: dict[str, Any], required_fields: list[str]) -> None:
    missing_fields = [field for field in required_fields if field not in frontmatter]
    if missing_fields:
        raise ValidationError(f"Missing required frontmatter fields: {missing_fields}")


def _validate_editable_fields(proposed_item_type: str, field_updates: dict[str, Any]) -> None:
    try:
        allowed = EDITABLE_FIELDS_BY_TYPE[proposed_item_type]
    except KeyError:
        raise ValidationError(
            f"Unknown proposed_item_type '{proposed_item_type}'; expected one of "
            f"{sorted(EDITABLE_FIELDS_BY_TYPE)}"
        ) from None
    disallowed = set(field_updates) - allowed
    if disallowed:
        raise UneditableFieldError(
            f"Field(s) {sorted(disallowed)} are not editable for proposed_item_type '{proposed_item_type}'"
        )


def _validate_path_segments(path_segments: list[str] | None) -> None:
    if not path_segments:
        return
    for segment in path_segments:
        if not segment or "/" in segment or segment == "..":
            raise ValidationError(
                f"Invalid path segment {segment!r}: must be a non-empty component "
                "with no '/' and not equal to '..'"
            )


def _generate_assertion_id() -> str:
    return f"assert-{uuid.uuid4()}"


def _generate_entity_id() -> str:
    return f"entity-{uuid.uuid4()}"


def _generate_event_id() -> str:
    return f"event-{uuid.uuid4()}"


def _generate_relationship_id() -> str:
    return f"relationship-{uuid.uuid4()}"


def proposal_path(vault_root: Path, domain: str, proposal_id: str) -> Path:
    return vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"


def assertion_path(
    vault_root: Path,
    domain: str,
    assertion_id: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_path_segments(path_segments)
    if context is not None:
        _validate_path_segments([context])
    base = vault_root / domain / "assertions"
    if context is not None:
        base = base / context
    for segment in path_segments or []:
        base = base / segment
    return base / assertion_id / f"{assertion_id}.md"


def entity_path(
    vault_root: Path,
    domain: str,
    entity_id: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_path_segments(path_segments)
    if context is not None:
        _validate_path_segments([context])
    base = vault_root / domain / "entities"
    if context is not None:
        base = base / context
    for segment in path_segments or []:
        base = base / segment
    return base / entity_id / f"{entity_id}.md"


def event_path(
    vault_root: Path,
    domain: str,
    event_id: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_path_segments(path_segments)
    if context is not None:
        _validate_path_segments([context])
    base = vault_root / domain / "events"
    if context is not None:
        base = base / context
    for segment in path_segments or []:
        base = base / segment
    return base / event_id / f"{event_id}.md"


def relationship_path(
    vault_root: Path,
    domain: str,
    relationship_id: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_path_segments(path_segments)
    if context is not None:
        _validate_path_segments([context])
    base = vault_root / domain / "relationships"
    if context is not None:
        base = base / context
    for segment in path_segments or []:
        base = base / segment
    return base / relationship_id / f"{relationship_id}.md"


def source_path(vault_root: Path, domain: str, source_id: str) -> Path:
    return vault_root / domain / "sources" / source_id / f"{source_id}.md"


def proposal_history_dir(vault_root: Path, domain: str, proposal_id: str) -> Path:
    return proposal_path(vault_root, domain, proposal_id).parent / "history"


@contextlib.contextmanager
def proposal_edit_lock(vault_root: Path, domain: str, proposal_id: str):
    """Serializes edit_proposal calls for a single proposal.

    Without this, two concurrent edits can both read the same next history
    version before either writes, archiving two different snapshots under the
    same version number (silently violating INV-004). A lock file older than
    _EDIT_LOCK_STALE_SECONDS is assumed to be left behind by a crashed process
    and is stolen rather than waited on forever.
    """
    lock_path = proposal_path(vault_root, domain, proposal_id).parent / ".edit.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + _EDIT_LOCK_TIMEOUT_SECONDS
    while True:
        try:
            os.close(os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lock_path) > _EDIT_LOCK_STALE_SECONDS:
                    os.remove(lock_path)
                    continue
            except OSError:
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for edit lock on proposal '{proposal_id}'")
            time.sleep(_EDIT_LOCK_POLL_SECONDS)
    try:
        yield
    finally:
        try:
            os.remove(lock_path)
        except OSError:
            pass


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


# Type-plural directory name and the _generate_*_id prefix that marks a leaf
# (an item's own id folder, not a taxonomy segment) for each of the four
# canonical item types (TASK-005a, ADI-012 adoption by entity/event/relationship).
_ORGANIZATION_ITEM_TYPE_DIRS = {
    "assertion": ("assertions", "assert-"),
    "entity": ("entities", "entity-"),
    "event": ("events", "event-"),
    "relationship": ("relationships", "relationship-"),
}


def scan_organization_folders(
    vault_root: Path, domain: str, item_type: str = "assertion"
) -> list[list[str]]:
    """Distinct taxonomy segment names under <domain>/<item-type-plural>/, grouped by
    depth (index 0 = segments directly under the type folder, etc).

    A directory named with that type's own _generate_*_id prefix is an item's own id
    folder - a leaf, not a taxonomy segment, and not descended into further.
    """
    dir_name, id_prefix = _ORGANIZATION_ITEM_TYPE_DIRS[item_type]
    type_dir = vault_root / domain / dir_name
    if not type_dir.exists():
        return []
    segments_by_depth: list[set[str]] = []

    def _walk(directory: Path, depth: int) -> None:
        for entry in sorted(directory.iterdir()):
            if not entry.is_dir() or entry.name.startswith(id_prefix):
                continue
            if len(segments_by_depth) <= depth:
                segments_by_depth.append(set())
            segments_by_depth[depth].add(entry.name)
            _walk(entry, depth + 1)

    _walk(type_dir, 0)
    return [sorted(depth_segments) for depth_segments in segments_by_depth]


def scan_existing_contexts(vault_root: Path, domain: str) -> list[str]:
    """Distinct non-null `context` frontmatter values across every Proposal under
    <domain>/proposals/, regardless of proposal_status or proposed_item_type (ADI-016/
    TASK-014a: context is cross-type; accept_proposal never deletes/moves the proposal file, so
    proposals/ stays a complete, non-lossy source even for already-ACCEPTED/REJECTED proposals).
    A malformed proposal file is skipped, not raised - same tolerance posture as
    ingestion/storage.py::scan_proposed_path_segments. Returns [] if proposals/ doesn't exist.
    """
    proposals_dir = vault_root / domain / "proposals"
    if not proposals_dir.exists():
        return []
    contexts: set[str] = set()
    for proposal_file in proposals_dir.glob("*/*.md"):
        try:
            frontmatter, _ = parse_frontmatter(proposal_file.read_text(encoding="utf-8"))
        except (OSError, ValidationError):
            continue
        context = frontmatter.get("context")
        if context:
            contexts.add(context)
    return sorted(contexts)


def write_assertion_file(
    vault_root: Path,
    domain: str,
    frontmatter: dict[str, Any],
    body: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_frontmatter(frontmatter, REQUIRED_ASSERTION_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_ASSERTION_PROVENANCE_FIELDS)

    path = assertion_path(
        vault_root, domain, frontmatter["id"], path_segments=path_segments, context=context
    )
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def write_entity_file(
    vault_root: Path,
    domain: str,
    frontmatter: dict[str, Any],
    body: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_frontmatter(frontmatter, REQUIRED_ENTITY_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_ASSERTION_PROVENANCE_FIELDS)

    path = entity_path(
        vault_root, domain, frontmatter["id"], path_segments=path_segments, context=context
    )
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def write_event_file(
    vault_root: Path,
    domain: str,
    frontmatter: dict[str, Any],
    body: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_frontmatter(frontmatter, REQUIRED_EVENT_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_ASSERTION_PROVENANCE_FIELDS)

    path = event_path(
        vault_root, domain, frontmatter["id"], path_segments=path_segments, context=context
    )
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def write_relationship_file(
    vault_root: Path,
    domain: str,
    frontmatter: dict[str, Any],
    body: str,
    path_segments: list[str] | None = None,
    context: str | None = None,
) -> Path:
    _validate_frontmatter(frontmatter, REQUIRED_RELATIONSHIP_FIELDS)
    _validate_frontmatter(frontmatter["provenance"], REQUIRED_ASSERTION_PROVENANCE_FIELDS)

    path = relationship_path(
        vault_root, domain, frontmatter["id"], path_segments=path_segments, context=context
    )
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def write_proposal_file_in_place(
    vault_root: Path, domain: str, proposal_id: str, frontmatter: dict[str, Any], body: str
) -> Path:
    path = proposal_path(vault_root, domain, proposal_id)
    _write_atomic_file(path, serialize_frontmatter(frontmatter, body))
    return path


def _next_history_version(history_dir: Path) -> int:
    """Version number for the snapshot about to be archived (n).

    Derived by parsing existing v<n> filenames rather than counting files, so a
    stray or malformed file in history/ can't skew numbering.
    """
    if not history_dir.exists():
        return 1
    versions = [
        int(match.group(1))
        for entry in history_dir.iterdir()
        if entry.is_file() and (match := _HISTORY_FILENAME_VERSION_RE.search(entry.name))
    ]
    return max(versions, default=0) + 1


def archive_proposal_version(
    vault_root: Path, domain: str, proposal_id: str, frontmatter: dict[str, Any], body: str
) -> tuple[Path, int]:
    """Archive the given (pre-edit) frontmatter+body as the next history snapshot.

    Must be called, and complete, before the live proposal file is overwritten
    (INV-019 ordering, enforced by caller order in pipeline.py).
    """
    history_dir = proposal_history_dir(vault_root, domain, proposal_id)
    version = _next_history_version(history_dir)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")

    snapshot_frontmatter = dict(frontmatter)
    snapshot_frontmatter["lifecycle_status"] = "SUPERSEDED"
    snapshot_frontmatter["superseded_by"] = f"v{version + 1}"

    path = history_dir / f"{timestamp}--v{version}.md"
    _write_atomic_file(path, serialize_frontmatter(snapshot_frontmatter, body))
    return path, version
