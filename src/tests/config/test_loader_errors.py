"""
AC4: a malformed YAML file, or a present-but-invalid value, raises a typed
ConfigError before load_config() returns - never a silent fallback for a
value that was actually present.
"""
import pytest

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import ConfigError, load_config


def test_malformed_yaml_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider: [unclosed\n  active: ollama", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_unknown_provider_active_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  active: gpt5\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_non_numeric_timeout_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    timeout: not-a-number\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_non_numeric_temperature_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    temperature: hot\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_negative_temperature_from_file_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    temperature: -0.1\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_zero_temperature_from_file_is_accepted(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    temperature: 0\n", encoding="utf-8")

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.ollama.temperature == 0.0


def test_non_numeric_temperature_via_env_var_raises_config_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TEMPERATURE", "hot")

    with pytest.raises(ConfigError):
        load_config(path=tmp_path / "does_not_exist.yaml")


def test_negative_temperature_via_env_var_raises_config_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TEMPERATURE", "-0.1")

    with pytest.raises(ConfigError):
        load_config(path=tmp_path / "does_not_exist.yaml")


def test_unknown_provider_via_env_var_raises_config_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PEKOPEKO_LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(ConfigError):
        load_config(path=tmp_path / "does_not_exist.yaml")


def test_non_numeric_timeout_via_env_var_raises_config_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TIMEOUT", "not-a-number")

    with pytest.raises(ConfigError):
        load_config(path=tmp_path / "does_not_exist.yaml")


def test_empty_yaml_file_is_treated_as_no_overrides(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("", encoding="utf-8")

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.active == "ollama"


def test_non_mapping_top_level_yaml_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


@pytest.mark.parametrize(
    "yaml_content",
    [
        "llm_provider: 5\n",
        "llm_provider:\n  ollama: 5\n",
        "retrieval: 5\n",
        "task_state: 5\n",
        "default: 5\n",
    ],
)
def test_non_mapping_nested_section_raises_config_error(tmp_path, yaml_content):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_negative_timeout_from_file_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    timeout: -5\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_zero_timeout_from_file_raises_config_error(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    timeout: 0\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(path=config_file)


def test_negative_timeout_via_env_var_raises_config_error(tmp_path, monkeypatch):
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TIMEOUT", "-5")

    with pytest.raises(ConfigError):
        load_config(path=tmp_path / "does_not_exist.yaml")
