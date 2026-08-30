"""
AC2: a YAML file that sets only a subset of keys applies a partial override -
keys absent from the file keep their built-in default. One key per
top-level section is verified.
"""
from pathlib import Path

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import load_config


def test_partial_override_llm_provider_ollama_model(tmp_path, monkeypatch):
    monkeypatch.delenv("PEKOPEKO_OLLAMA_MODEL", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "llm_provider:\n  ollama:\n    model: mistral\n",
        encoding="utf-8",
    )

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.ollama.model == "mistral"
    # Rest of the section keeps its built-in default.
    assert cfg.llm_provider.active == "ollama"
    assert cfg.llm_provider.ollama.base_url == "http://localhost:11434"
    assert cfg.llm_provider.ollama.timeout == 60


def test_partial_override_retrieval_index_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("PEKOPEKO_RETRIEVAL_INDEX_DIR", raising=False)
    custom_index_dir = tmp_path / "custom_index"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"retrieval:\n  index_dir: {custom_index_dir.as_posix()}\n",
        encoding="utf-8",
    )

    cfg = load_config(path=config_file)

    assert cfg.retrieval.index_dir == custom_index_dir
    assert cfg.task_state.dir == Path.home() / ".pekopeko" / "task_state"


def test_partial_override_task_state_dir(tmp_path, monkeypatch):
    monkeypatch.delenv("PEKOPEKO_TASK_STATE_DIR", raising=False)
    custom_state_dir = tmp_path / "custom_state"
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"task_state:\n  dir: {custom_state_dir.as_posix()}\n",
        encoding="utf-8",
    )

    cfg = load_config(path=config_file)

    assert cfg.task_state.dir == custom_state_dir
    assert cfg.retrieval.index_dir == Path.home() / ".pekopeko" / "retrieval_index"


def test_partial_override_default_domain(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("default:\n  domain: FICTION\n", encoding="utf-8")

    cfg = load_config(path=config_file)

    assert cfg.default.domain == "FICTION"


def test_default_domain_falls_back_when_absent(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    model: mistral\n", encoding="utf-8")

    cfg = load_config(path=config_file)

    assert cfg.default.domain == "PERSONAL"
