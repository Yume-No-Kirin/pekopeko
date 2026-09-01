"""
Extraction endpoints (async, ADI-010 SS2) - identical shape to routes_ingestion.py,
kept as a separate mirrored module (extraction never imports ingestion's code,
this project's established module-independence convention).
"""
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from ..config import load_config
from ..extraction.errors import InvalidDomainError
from ..extraction.pipeline import extract_source
from ..extraction.providers.factory import build_configured_provider
from ..extraction.task_state import create_task_state, list_task_states, load_task_state, update_task_state
from . import serialization
from .domains import VALID_DOMAINS
from .tasks import load_task_state_resilient, run_in_background

extraction_bp = Blueprint("extraction", __name__)


def _state_dir():
    return load_config().task_state.dir / "extraction"


def _vault_root():
    return current_app.config["PEKOPEKO_SETTINGS"].vault_root


@extraction_bp.route("/domains/<domain>/extractions", methods=["POST"])
def start_extraction(domain):
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    body = request.get_json(silent=True) or {}
    source_path = body.get("source_path")
    if not source_path:
        raise ValueError("source_path is required")

    config = load_config()
    state_dir = config.task_state.dir / "extraction"
    task_id = f"extract-{uuid.uuid4()}"
    provider = build_configured_provider(config)

    task_state = create_task_state(source_path, domain, state_dir, task_id=task_id)
    update_task_state(task_state, state_dir)

    run_in_background(
        extract_source, _vault_root(), domain, Path(source_path), provider, state_dir, task_id
    )

    return jsonify({"task_id": task_id, "status": "pending"}), 202


@extraction_bp.route("/domains/<domain>/extractions/<task_id>", methods=["GET"])
def get_extraction(domain, task_id):
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    task_state = load_task_state_resilient(load_task_state, _state_dir(), task_id)
    if task_state is None or task_state.domain != domain:
        return jsonify({"error": {"type": "TaskNotFoundError", "message": f"Task '{task_id}' not found"}}), 404

    return jsonify(serialization.task_state_to_dict(task_state)), 200


@extraction_bp.route("/domains/<domain>/extractions", methods=["GET"])
def list_extractions(domain):
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")

    status = request.args.get("status")
    states = [
        s for s in list_task_states(_state_dir())
        if s.domain == domain and (status is None or s.status == status)
    ]
    return jsonify([serialization.task_state_to_dict(s) for s in states]), 200
