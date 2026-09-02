"""
Typed exceptions for the api/ orchestration layer itself (as opposed to
errors raised by ingestion/extraction/review and re-mapped in app.py).
"""


class ApiError(Exception):
    """Base class for exceptions raised by the api/ orchestration layer itself."""


class ValidationError(ApiError):
    """Raised for invalid pagination query parameters (limit/offset)."""
