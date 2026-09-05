"""
Review endpoints (sync, ADI-010 SS3): thin pass-through to
review.list_proposals/get_proposal/accept_proposal/reject_proposal - no
reimplementation, no change to review/'s public contract.
"""
from flask import Blueprint, current_app, jsonify, request

from ..review import storage
from ..review.errors import InvalidDomainError, ValidationError
from ..review.pipeline import accept_proposal, edit_proposal, get_proposal, list_proposals, reject_proposal
from . import serialization
from .domains import VALID_DOMAINS

review_bp = Blueprint("review", __name__)

_VALID_ORGANIZATION_ITEM_TYPES = {"assertion"}


def _vault_root():
    return current_app.config["PEKOPEKO_SETTINGS"].vault_root


def _check_domain(domain):
    if domain not in VALID_DOMAINS:
        raise InvalidDomainError(f"Invalid domain '{domain}'. Must be one of {sorted(VALID_DOMAINS)}")


@review_bp.route("/domains/<domain>/proposals", methods=["GET"])
def get_proposals(domain):
    _check_domain(domain)
    limit, offset = serialization.parse_pagination_args(request.args)
    status = request.args.get("status")
    summaries = list_proposals(_vault_root(), domain, status=status)
    serialization.sort_by_recency(summaries, "created_at")
    return jsonify(serialization.paginated_response(summaries, limit, offset, serialization.proposal_summary_to_dict)), 200


@review_bp.route("/domains/<domain>/proposals/<proposal_id>", methods=["GET"])
def get_proposal_detail(domain, proposal_id):
    _check_domain(domain)
    detail = get_proposal(_vault_root(), domain, proposal_id)
    return jsonify(serialization.proposal_detail_to_dict(detail)), 200


@review_bp.route("/domains/<domain>/proposals/<proposal_id>/accept", methods=["POST"])
def accept(domain, proposal_id):
    _check_domain(domain)
    body = request.get_json(silent=True) or {}
    reviewer_id = body.get("reviewer_id")
    result = accept_proposal(_vault_root(), domain, proposal_id, reviewer_id)
    return jsonify(serialization.accept_result_to_dict(result)), 200


@review_bp.route("/domains/<domain>/proposals/<proposal_id>/reject", methods=["POST"])
def reject(domain, proposal_id):
    _check_domain(domain)
    body = request.get_json(silent=True) or {}
    reviewer_id = body.get("reviewer_id")
    reason = body.get("reason")
    result = reject_proposal(_vault_root(), domain, proposal_id, reviewer_id, reason=reason)
    return jsonify(serialization.reject_result_to_dict(result)), 200


@review_bp.route("/domains/<domain>/proposals/<proposal_id>/edit", methods=["POST"])
def edit(domain, proposal_id):
    _check_domain(domain)
    body = request.get_json(silent=True) or {}
    reviewer_id = body.get("reviewer_id")
    result = edit_proposal(
        _vault_root(), domain, proposal_id, reviewer_id,
        body=body.get("body"), field_updates=body.get("field_updates"),
    )
    return jsonify(serialization.edit_result_to_dict(result)), 200


@review_bp.route("/domains/<domain>/organization-folders", methods=["GET"])
def get_organization_folders(domain):
    _check_domain(domain)
    item_type = request.args.get("item_type")
    if item_type not in _VALID_ORGANIZATION_ITEM_TYPES:
        raise ValidationError(
            f"item_type must be one of {sorted(_VALID_ORGANIZATION_ITEM_TYPES)}, got {item_type!r}"
        )
    segments_by_depth = storage.scan_organization_folders(_vault_root(), domain)
    return jsonify(serialization.organization_folders_to_dict(segments_by_depth)), 200
