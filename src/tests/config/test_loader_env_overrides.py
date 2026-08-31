"""
AC5: each environment-variable override in the bounded list takes precedence
over the corresponding file value when both are set. One test per
top-level section: provider, retrieval, task_state.
"""
from pathlib import Path

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import load_config


def _write_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm_provider:\n"
        "  active: ollama\n"
        "  ollama:\n"
        "    base_url: http://file-value:11434\n"
        "    model: file-model\n"
        "    timeout: 30\n"
        "    temperature: 0.3\n"
        "retrieval:\n"
        "  index_dir: /file/index_dir\n"
        "task_state:\n"
        "  dir: /file/task_state_dir\n",
        encoding="utf-8",
    )
    return config_file


def test_provider_env_overrides_take_precedence_over_file(tmp_path, monkeypatch):
    config_file = _write_config(tmp_path)
    monkeypatch.setenv("PEKOPEKO_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_MODEL", "env-model")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_BASE_URL", "http://env-value:11434")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TIMEOUT", "90")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_TEMPERATURE", "0.9")

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.active == "ollama"
    assert cfg.llm_provider.ollama.model == "env-model"
    assert cfg.llm_provider.ollama.base_url == "http://env-value:11434"
    assert cfg.llm_provider.ollama.timeout == 90
    assert cfg.llm_provider.ollama.temperature == 0.9


def test_retrieval_env_override_takes_precedence_over_file(tmp_path, monkeypatch):
    config_file = _write_config(tmp_path)
    env_index_dir = tmp_path / "env_index_dir"
    monkeypatch.setenv("PEKOPEKO_RETRIEVAL_INDEX_DIR", str(env_index_dir))

    cfg = load_config(path=config_file)

    assert cfg.retrieval.index_dir == env_index_dir


def test_task_state_env_override_takes_precedence_over_file(tmp_path, monkeypatch):
    config_file = _write_config(tmp_path)
    env_state_dir = tmp_path / "env_state_dir"
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(env_state_dir))

    cfg = load_config(path=config_file)

    assert cfg.task_state.dir == env_state_dir


def test_empty_string_env_var_is_treated_as_unset(tmp_path, monkeypatch):
    config_file = _write_config(tmp_path)
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", "")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_MODEL", "")
    monkeypatch.setenv("PEKOPEKO_LLM_PROVIDER", "")

    cfg = load_config(path=config_file)

    # Falls through to the file value, not Path("").expanduser() (cwd) or "".
    assert cfg.task_state.dir == Path("/file/task_state_dir")
    assert cfg.llm_provider.ollama.model == "file-model"
    assert cfg.llm_provider.active == "ollama"
