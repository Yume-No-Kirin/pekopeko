"""
Flask app factory for the Pekopeko backend API (ADI-010): registers all
route blueprints, the X-API-Key check, a manual CORS header, and the single
JSON error envelope mapped from each typed exception per the ticket's error
mapping table.
"""
from typing import Optional

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from ..config.errors import ConfigError
from ..extraction.errors import InvalidDomainError as ExtractionInvalidDomainError
from ..extraction.errors import ValidationError as ExtractionValidationError
from ..review.errors import DomainMismatchError
from ..review.errors import InvalidDomainError as ReviewInvalidDomainError
from ..review.errors import (
    InvalidProposalStatusError,
    ProposalNotFoundError,
    SourceNotFoundError,
    UnsupportedProposalTypeError,
)
from ..review.errors import ValidationError as ReviewValidationError
from .routes_config import config_bp
from .routes_extraction import extraction_bp
from .routes_ingestion import ingestion_bp
from .routes_review import review_bp
from .settings import ApiSettings, load_settings

# Exception class -> HTTP status, per TASK-007's Error mapping table.
ERROR_STATUS_MAP = {
    ValueError: 400,
    ExtractionInvalidDomainError: 400,
    ReviewInvalidDomainError: 400,
    ExtractionValidationError: 400,
    ReviewValidationError: 400,
    ProposalNotFoundError: 404,
    SourceNotFoundError: 404,
    DomainMismatchError: 400,
    InvalidProposalStatusError: 409,
    UnsupportedProposalTypeError: 422,
    ConfigError: 500,
}


def _error_response(error_type: str, message: str, status: int):
    return jsonify({"error": {"type": error_type, "message": message}}), status


def create_app(settings: Optional[ApiSettings] = None) -> Flask:
    app = Flask(__name__)
    app.config["PEKOPEKO_SETTINGS"] = settings or load_settings()

    app.register_blueprint(ingestion_bp)
    app.register_blueprint(extraction_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(config_bp)

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
