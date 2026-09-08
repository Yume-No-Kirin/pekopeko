"""
Flask app factory for the Pekopeko backend API (ADI-010): registers all
route blueprints, the X-API-Key check, a manual CORS header, and the single
JSON error envelope mapped from each typed exception per the ticket's error
mapping table.
"""
from typing import Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from ..config import load_config
from ..config.errors import ConfigError
from ..extraction.errors import InvalidDomainError as ExtractionInvalidDomainError
from ..extraction.errors import ValidationError as ExtractionValidationError
from ..review.errors import DomainMismatchError
from ..review.errors import InvalidDomainError as ReviewInvalidDomainError
from ..review.errors import (
    InvalidProposalStatusError,
    ProposalNotFoundError,
    SourceNotFoundError,
    UneditableFieldError,
    UnresolvedRelationshipEndpointError,
    UnsupportedProposalTypeError,
)
from ..review.errors import ValidationError as ReviewValidationError
from .errors import ValidationError as PaginationValidationError
from .routes_config import config_bp
from .routes_extraction import extraction_bp
from .routes_ingestion import ingestion_bp
from .routes_review import review_bp
from .settings import ApiSettings, load_settings
from ..ingestion.providers.factory import build_configured_provider
from ..ingestion.watcher import start_folder_watcher

# Exception class -> HTTP status, per TASK-007's Error mapping table.
ERROR_STATUS_MAP = {
    ValueError: 400,
    ExtractionInvalidDomainError: 400,
    ReviewInvalidDomainError: 400,
    ExtractionValidationError: 400,
    ReviewValidationError: 400,
    PaginationValidationError: 400,
    ProposalNotFoundError: 404,
    SourceNotFoundError: 404,
    DomainMismatchError: 400,
    InvalidProposalStatusError: 409,
    UnresolvedRelationshipEndpointError: 409,
    UneditableFieldError: 400,
    UnsupportedProposalTypeError: 422,
    ConfigError: 500,
}


def _error_response(error_type: str, message: str, status: int):
    return jsonify({"error": {"type": error_type, "message": message}}), status


def create_app(settings: Optional[ApiSettings] = None) -> Flask:
    app = Flask(__name__)
    resolved_settings = settings or load_settings()
    app.config["PEKOPEKO_SETTINGS"] = resolved_settings

    app.register_blueprint(ingestion_bp)
    app.register_blueprint(extraction_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(config_bp)

    # ADI-013/TASK-001f/TASK-014b: no-ops unless folder_watch.enabled is set
    # in config.yaml. Provider construction (build_configured_provider) is
    # itself gated on `enabled` here, not left to start_folder_watcher's own
    # no-op check, so a disabled watcher never pays the cost of eagerly
    # constructing a provider (or surfacing a provider-construction failure,
    # e.g. a missing `requests` install) at app-factory time for a feature
    # that isn't even turned on.
    config = load_config()
    if config.folder_watch.enabled:
        start_folder_watcher(
            config, resolved_settings.vault_root, build_configured_provider(config),
            config.task_state.dir / "ingestion",
        )

    @app.before_request
    def check_api_key():
        if request.method == "OPTIONS":
            return None
        api_settings: ApiSettings = app.config["PEKOPEKO_SETTINGS"]
        provided = request.headers.get("X-API-Key")
        if provided != api_settings.api_key:
            return _error_response("Unauthorized", "Missing or invalid X-API-Key header", 401)

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "X-API-Key, Content-Type"
        return response

    def _make_handler(status):
        def handler(e):
            return _error_response(type(e).__name__, str(e), status)
        return handler

    for exc_type, status in ERROR_STATUS_MAP.items():
        app.register_error_handler(exc_type, _make_handler(status))

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        if isinstance(e, HTTPException):
            return _error_response(type(e).__name__, e.description or str(e), e.code or 500)
        return _error_response(type(e).__name__, str(e), 500)

    return app


def main() -> None:
    app = create_app()
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
