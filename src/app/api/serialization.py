"""
JSON-dict helpers for the result/state objects returned by ingestion,
extraction, review, and config, so route handlers never build JSON bodies by
hand. IngestionResult/ExtractionPipelineResult/TaskState are plain classes
(not @dataclass) - hand-written here; ProposalSummary/ProposalDetail/
AcceptResult/RejectResult/PekopekoConfig are @dataclass, via
dataclasses.asdict. Path fields are converted to str throughout - JSON has
no Path type.
"""
from dataclasses import asdict
from operator import attrgetter
from typing import Any, Callable, Dict, Tuple

from .errors import ValidationError

DEFAULT_LIMIT = 50
MIN_LIMIT = 1
MAX_LIMIT = 500
DEFAULT_OFFSET = 0


def parse_pagination_args(args) -> Tuple[int, int]:
    """Reads limit/offset from a Flask request.args-like mapping, applying
    the documented defaults (50, 0). Raises ValidationError on a
    non-integer value, limit outside [1, 500], or a negative offset."""
    limit_raw = args.get("limit")
    if limit_raw is None:
        limit = DEFAULT_LIMIT
    else:
        try:
            limit = int(limit_raw)
        except ValueError:
            raise ValidationError(f"limit must be an integer, got {limit_raw!r}")
        if not (MIN_LIMIT <= limit <= MAX_LIMIT):
            raise ValidationError(f"limit must be between {MIN_LIMIT} and {MAX_LIMIT}, got {limit}")

    offset_raw = args.get("offset")
    if offset_raw is None:
        offset = DEFAULT_OFFSET
    else:
        try:
            offset = int(offset_raw)
        except ValueError:
            raise ValidationError(f"offset must be an integer, got {offset_raw!r}")
        if offset < 0:
            raise ValidationError(f"offset must be >= 0, got {offset}")

    return limit, offset


def paginate(items: list, limit: int, offset: int) -> Dict[str, Any]:
    """Slices an already-sorted list into one page plus the envelope
    metadata. `items` in the result are the raw sliced objects, not yet
    serialized to dicts - the caller applies its own per-item serializer."""
    return {
        "items": items[offset:offset + limit],
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


def sort_by_recency(items: list, field: str) -> list:
    """Sorts `items` newest-first in place by the named timestamp attribute.
    Centralizes the field-name lookup so a rename on the underlying dataclass
    only needs fixing at each call site's field argument, not the sort logic."""
    items.sort(key=attrgetter(field), reverse=True)
    return items


def paginated_response(items: list, limit: int, offset: int, serializer: Callable[[Any], Dict[str, Any]]) -> Dict[str, Any]:
    """Builds the full list-endpoint JSON envelope: paginates `items` then
    applies `serializer` to just the sliced page."""
    page = paginate(items, limit, offset)
    return {
        "items": [serializer(item) for item in page["items"]],
        "total": page["total"],
        "limit": page["limit"],
        "offset": page["offset"],
    }


def ingestion_result_to_dict(result) -> Dict[str, Any]:
    return {
        "source_id": result.source_id,
        "proposal_ids": result.proposal_ids,
        "status": result.status,
        "error": result.error,
        "skipped_duplicate": result.skipped_duplicate,
    }


def extraction_result_to_dict(result) -> Dict[str, Any]:
    return {
        "source_id": result.source_id,
        "proposal_ids": result.proposal_ids,
        "status": result.status,
        "error": result.error,
        "skipped_duplicate": result.skipped_duplicate,
    }


def task_state_to_dict(task_state) -> Dict[str, Any]:
    # TaskState already implements to_dict() (ingestion/extraction task_state.py),
    # including nested TaskEvent serialization - reused verbatim.
    return task_state.to_dict()


def proposal_summary_to_dict(summary) -> Dict[str, Any]:
    return asdict(summary)


def proposal_detail_to_dict(detail) -> Dict[str, Any]:
    return asdict(detail)


def accept_result_to_dict(result) -> Dict[str, Any]:
    data = asdict(result)
    data["assertion_path"] = str(result.assertion_path)
    return data


def reject_result_to_dict(result) -> Dict[str, Any]:
    return asdict(result)


def config_to_dict(cfg) -> Dict[str, Any]:
    data = asdict(cfg)
    data["retrieval"]["index_dir"] = str(cfg.retrieval.index_dir)
    data["task_state"]["dir"] = str(cfg.task_state.dir)
    return data
