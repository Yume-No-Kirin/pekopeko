"""
Typed exceptions for the entity/event/relationship extraction pipeline.
"""


class ExtractionError(Exception):
    """Base class for all extraction/ module errors."""


class InvalidDomainError(ExtractionError):
    """Raised when domain is not one of the allowed domains."""


class ValidationError(ExtractionError):
    """Raised when frontmatter is missing/invalid, before any file is written."""
