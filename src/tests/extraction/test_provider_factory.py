"""
AC6/AC7/AC11: extraction.providers.factory.build_configured_provider maps a
loaded config to a concrete OllamaProvider, without any real network call,
and raises a typed error for an unknown provider name. Also confirms
extract_source()'s public signature is unchanged.
"""
import inspect

import pytest

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import ConfigError, LLMProviderConfig, OllamaProviderSettings, PekopekoConfig
from src.app.extraction.pipeline import extract_source
from src.app.extraction.providers.factory import build_configured_provider
from src.app.extraction.providers.ollama_provider import OllamaProvider


def _config_with(active: str) -> PekopekoConfig:
    return PekopekoConfig(
        llm_provider=LLMProviderConfig(
            active=active,
            ollama=OllamaProviderSettings(base_url="http://example:11434", model="phi3", timeout=45),
        )
    )


def test_build_configured_provider_returns_ollama_provider():
    cfg = _config_with("ollama")

    provider = build_configured_provider(cfg)

    assert isinstance(provider, OllamaProvider)
    assert provider.config.base_url == "http://example:11434"
    assert provider.config.model == "phi3"
    assert provider.config.timeout == 45


def test_build_configured_provider_raises_on_unknown_provider():
    cfg = _config_with("unknown-provider")

    with pytest.raises(ConfigError):
        build_configured_provider(cfg)


def test_extract_source_signature_is_unchanged():
    params = list(inspect.signature(extract_source).parameters)
    assert params == ["vault_root", "domain", "source_path", "provider", "state_dir", "task_id"]
