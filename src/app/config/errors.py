"""
Typed exceptions for the app/config module.
"""


class ConfigError(Exception):
    """Raised when a config file is malformed or a present value fails schema validation."""
