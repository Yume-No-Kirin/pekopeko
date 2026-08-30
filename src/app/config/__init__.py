"""
Local device configuration for Pekopeko (ADI-008).

Dependency-free with respect to the rest of app/ - pipelines depend on this
module, never the reverse.
"""
from .errors import ConfigError
from .loader import load_config
from .schema import (
    DefaultConfig,
    LLMProviderConfig,
    OllamaProviderSettings,
    PekopekoConfig,
    RetrievalConfig,
    TaskStateConfig,
)

__all__ = [
    'load_config',
    'PekopekoConfig',
    'LLMProviderConfig',
    'OllamaProviderSettings',
    'RetrievalConfig',
    'TaskStateConfig',
    'DefaultConfig',
    'ConfigError',
]
