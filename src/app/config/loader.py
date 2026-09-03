"""
Loader for the Pekopeko local device configuration (ADI-008).

Resolution order: explicit `path` argument > PEKOPEKO_CONFIG_PATH env var >
default <project>/src/config.yaml. A missing file (at any resolution step) is
not an error - built-in defaults are returned. A malformed file, or a
present-but-invalid value, raises ConfigError.
"""
import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from .errors import ConfigError
from .schema import (
    DefaultConfig,
    LLMProviderConfig,
    OllamaProviderSettings,
    PekopekoConfig,
    RetrievalConfig,
    TaskStateConfig,
)

# src/app/config/loader.py -> src/
_SRC_DIR = Path(__file__).resolve().parents[2]

VALID_PROVIDERS = frozenset({"ollama"})

_ENV_CONFIG_PATH = "PEKOPEKO_CONFIG_PATH"
_ENV_LLM_PROVIDER = "PEKOPEKO_LLM_PROVIDER"
_ENV_OLLAMA_BASE_URL = "PEKOPEKO_OLLAMA_BASE_URL"
_ENV_OLLAMA_MODEL = "PEKOPEKO_OLLAMA_MODEL"
_ENV_OLLAMA_TIMEOUT = "PEKOPEKO_OLLAMA_TIMEOUT"
_ENV_OLLAMA_TEMPERATURE = "PEKOPEKO_OLLAMA_TEMPERATURE"
_ENV_TASK_STATE_DIR = "PEKOPEKO_TASK_STATE_DIR"
_ENV_RETRIEVAL_INDEX_DIR = "PEKOPEKO_RETRIEVAL_INDEX_DIR"


def _resolve_path(path: Optional[Path]) -> Path:
    if path is not None:
        return path
    env_path = os.environ.get(_ENV_CONFIG_PATH)
    if env_path:
        return Path(env_path)
    return _SRC_DIR / "config.yaml"


def _load_dotenv(resolved_path: Path) -> None:
    """
    Optional companion .env file, next to the resolved config.yaml, for
    secrets/sensitive values. Loads into os.environ without overriding a
    real process env var already set (override=False), so it only fills in
    the bounded PEKOPEKO_* keys that weren't already set another way. A
    missing .env is not an error - it's supplementary, not mandatory.
    """
    load_dotenv(dotenv_path=resolved_path.parent / ".env", override=False)


def _read_file(resolved_path: Path) -> dict:
    if not resolved_path.exists():
        return {}
    try:
        raw = resolved_path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ConfigError(f"Malformed YAML in config file {resolved_path}: {e}") from e
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file {resolved_path} must contain a YAML mapping at the top level")
    return data


def _require_mapping(data: dict, key: str, label: Optional[str] = None) -> dict:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"Config key {label or key!r} must be a mapping, got {value!r}")
    return value


def _validate_timeout(raw_timeout) -> int:
    if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, int):
        raise ConfigError(f"llm_provider.ollama.timeout must be an integer, got {raw_timeout!r}")
    if raw_timeout <= 0:
        raise ConfigError(f"llm_provider.ollama.timeout must be a positive integer, got {raw_timeout!r}")
    return raw_timeout


def _validate_temperature(raw_temperature) -> float:
    if isinstance(raw_temperature, bool) or not isinstance(raw_temperature, (int, float)):
        raise ConfigError(f"llm_provider.ollama.temperature must be a number, got {raw_temperature!r}")
    if raw_temperature < 0:
        raise ConfigError(f"llm_provider.ollama.temperature must be >= 0, got {raw_temperature!r}")
    return float(raw_temperature)


def _validate_provider(active: str) -> str:
    if active not in VALID_PROVIDERS:
        raise ConfigError(
            f"Unknown llm_provider.active {active!r}. Must be one of {sorted(VALID_PROVIDERS)}"
        )
    return active


def _build_config(file_data: dict) -> PekopekoConfig:
    llm_provider_data = _require_mapping(file_data, "llm_provider")
    ollama_data = _require_mapping(llm_provider_data, "ollama", label="llm_provider.ollama")
    retrieval_data = _require_mapping(file_data, "retrieval")
    task_state_data = _require_mapping(file_data, "task_state")

    ollama_defaults = OllamaProviderSettings()
    ollama = OllamaProviderSettings(
        base_url=ollama_data.get("base_url", ollama_defaults.base_url),
        model=ollama_data.get("model", ollama_defaults.model),
        timeout=_validate_timeout(ollama_data.get("timeout", ollama_defaults.timeout)),
        temperature=_validate_temperature(ollama_data.get("temperature", ollama_defaults.temperature)),
    )

    llm_provider_defaults = LLMProviderConfig()
    llm_provider = LLMProviderConfig(
        active=_validate_provider(llm_provider_data.get("active", llm_provider_defaults.active)),
        ollama=ollama,
    )

    retrieval_defaults = RetrievalConfig()
    retrieval = RetrievalConfig(
        index_dir=Path(retrieval_data.get("index_dir", retrieval_defaults.index_dir)).expanduser(),
    )

    task_state_defaults = TaskStateConfig()
    task_state = TaskStateConfig(
        dir=Path(task_state_data.get("dir", task_state_defaults.dir)).expanduser(),
    )

    default_data = _require_mapping(file_data, "default")
    default_defaults = DefaultConfig()
    default = DefaultConfig(
        domain=default_data.get("domain", default_defaults.domain),
    )

    return PekopekoConfig(llm_provider=llm_provider, retrieval=retrieval, task_state=task_state, default=default)


def _apply_env_overrides(cfg: PekopekoConfig) -> PekopekoConfig:
    # env.get(KEY) (truthy check) rather than `KEY in env`, throughout: an
    # env var present but set to "" is treated as unset, falling through to
    # the file/default value, instead of resolving to a garbage override
    # (e.g. Path("").expanduser() silently resolving to the cwd).
    env = os.environ

    active = cfg.llm_provider.active
    if env.get(_ENV_LLM_PROVIDER):
        active = _validate_provider(env[_ENV_LLM_PROVIDER])

    ollama = OllamaProviderSettings(
        base_url=env.get(_ENV_OLLAMA_BASE_URL) or cfg.llm_provider.ollama.base_url,
        model=env.get(_ENV_OLLAMA_MODEL) or cfg.llm_provider.ollama.model,
        timeout=(
            _validate_timeout_str(env[_ENV_OLLAMA_TIMEOUT])
            if env.get(_ENV_OLLAMA_TIMEOUT)
            else cfg.llm_provider.ollama.timeout
        ),
        temperature=(
            _validate_temperature_str(env[_ENV_OLLAMA_TEMPERATURE])
            if env.get(_ENV_OLLAMA_TEMPERATURE)
            else cfg.llm_provider.ollama.temperature
        ),
    )

    retrieval_index_dir = (
        Path(env[_ENV_RETRIEVAL_INDEX_DIR]).expanduser()
        if env.get(_ENV_RETRIEVAL_INDEX_DIR)
        else cfg.retrieval.index_dir
    )

    task_state_dir = (
        Path(env[_ENV_TASK_STATE_DIR]).expanduser()
        if env.get(_ENV_TASK_STATE_DIR)
        else cfg.task_state.dir
    )

    return PekopekoConfig(
        llm_provider=LLMProviderConfig(active=active, ollama=ollama),
        retrieval=RetrievalConfig(index_dir=retrieval_index_dir),
        task_state=TaskStateConfig(dir=task_state_dir),
        default=cfg.default,
    )


def _validate_timeout_str(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as e:
        raise ConfigError(f"{_ENV_OLLAMA_TIMEOUT} must be an integer, got {raw!r}") from e
    if value <= 0:
        raise ConfigError(f"{_ENV_OLLAMA_TIMEOUT} must be a positive integer, got {raw!r}")
    return value


def _validate_temperature_str(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError as e:
        raise ConfigError(f"{_ENV_OLLAMA_TEMPERATURE} must be a number, got {raw!r}") from e
    if value < 0:
        raise ConfigError(f"{_ENV_OLLAMA_TEMPERATURE} must be >= 0, got {raw!r}")
    return value


def load_config(path: Optional[Path] = None) -> PekopekoConfig:
    resolved_path = _resolve_path(path)
    _load_dotenv(resolved_path)
    file_data = _read_file(resolved_path)
    cfg = _build_config(file_data)
    return _apply_env_overrides(cfg)
