"""
Provider-construction helper: maps a loaded config to a concrete ingestion
Provider. Used by callers of ingest_source(), never by pipeline.py itself.
"""
from ...config import ConfigError, PekopekoConfig
from .base import Provider
from .ollama_provider import OllamaProvider, OllamaProviderConfig


def build_configured_provider(cfg: PekopekoConfig) -> Provider:
    active = cfg.llm_provider.active
    if active == "ollama":
        ollama_cfg = cfg.llm_provider.ollama
        return OllamaProvider(
            OllamaProviderConfig(
                base_url=ollama_cfg.base_url,
                model=ollama_cfg.model,
                timeout=ollama_cfg.timeout,
                temperature=ollama_cfg.temperature,
            )
        )
    raise ConfigError(f"ingestion has no provider implementation for llm_provider.active={active!r}")
