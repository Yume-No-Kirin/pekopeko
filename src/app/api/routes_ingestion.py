"""
Ingestion endpoints (async, ADI-010 SS2): POST starts a background
ingest_source() job and returns 202 with a task_id minted and persisted
synchronously before the response; GET polls the resulting TaskState.
"""
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..config import load_config
from ..ingestion.pipeline import ingest_source
from ..ingestion.providers.factory import build_configured_provider
from ..ingestion.task_state import create_task_state, list_task_states, load_task_state, update_task_state
from . import serialization
from .domains import VALID_DOMAINS
from .tasks import load_task_state_resilient, run_in_background

ingestion_bp = Blueprint("ingestion", __name__)


def _state_dir():
    return load_config().task_state.dir / "ingestion"


def _vault_root():
    return current_app.config["PEKOPEKO_SETTINGS"].vault_root


@ingestion_bp.route("/domains/<domain>/ingestions", methods=["POST"])
def start_ingestion(domain):
    if domain not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    body = request.get_json(silent=True) or {}
    source_path = body.get("source_path")
    if not source_path:
        raise ValueError("source_path is required")

    config = load_config()
    state_dir = config.task_state.dir / "ingestion"
    task_id = f"ingest-{uuid.uuid4()}"
    provider = build_configured_provider(config)

    task_state = create_task_state(source_path, domain, state_dir, task_id=task_id)
    update_task_state(task_state, state_dir)

    run_in_background(
        ingest_source, _vault_root(), domain, Path(source_path), provider, state_dir, task_id
    )

    return jsonify({"task_id": task_id, "status": "pending"}), 202


@ingestion_bp.route("/domains/<domain>/ingestions/<task_id>", methods=["GET"])
def get_ingestion(domain, task_id):
    if domain not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    task_state = load_task_state_resilient(load_task_state, _state_dir(), task_id)
    if task_state is None or task_state.domain != domain:
        return jsonify({"error": {"type": "TaskNotFoundError", "message": f"Task '{task_id}' not found"}}), 404

    return jsonify(serialization.task_state_to_dict(task_state)), 200


@ingestion_bp.route("/domains/<domain>/ingestions", methods=["GET"])
def list_ingestions(domain):
    if domain not in VALID_DOMAINS:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    limit, offset = serialization.parse_pagination_args(request.args)
    status = request.args.get("status")
    states = [
        s for s in list_task_states(_state_dir())
        if s.domain == domain and (status is None or s.status == status)
    ]
    serialization.sort_by_recency(states, "started_at")
    return jsonify(serialization.paginated_response(states, limit, offset, serialization.task_state_to_dict)), 200
