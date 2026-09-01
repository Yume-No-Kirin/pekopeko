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
from typing import Any, Dict


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
