"""
AC6/AC7/AC11: ingestion.providers.factory.build_configured_provider maps a
loaded config to a concrete OllamaProvider, without any real network call,
and raises a typed error for an unknown provider name. Also confirms
ingest_source()'s public signature is unchanged.
"""
import inspect

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.config import ConfigError, LLMProviderConfig, OllamaProviderSettings, PekopekoConfig
from src.app.ingestion.pipeline import ingest_source
from src.app.ingestion.providers.factory import build_configured_provider
from src.app.ingestion.providers.ollama_provider import OllamaProvider


def _config_with(active: str) -> PekopekoConfig:
    return PekopekoConfig(
        llm_provider=LLMProviderConfig(
            active=active,
            ollama=OllamaProviderSettings(base_url="http://example:11434", model="phi3", timeout=45, temperature=0.15),
        )
    )


def test_build_configured_provider_returns_ollama_provider():
    cfg = _config_with("ollama")

    provider = build_configured_provider(cfg)

    assert isinstance(provider, OllamaProvider)
    assert provider.config.base_url == "http://example:11434"
    assert provider.config.model == "phi3"
    assert provider.config.timeout == 45
    assert provider.config.temperature == 0.15


def test_build_configured_provider_raises_on_unknown_provider():
    cfg = _config_with("unknown-provider")

    with pytest.raises(ConfigError):
        build_configured_provider(cfg)


def test_ingest_source_signature_is_unchanged():
    params = list(inspect.signature(ingest_source).parameters)
    assert params == ["vault_root", "domain", "source_path", "provider", "state_dir"]
