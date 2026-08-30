"""
AC12: a companion .env file next to the resolved config.yaml is loaded into
os.environ (via python-dotenv) and its values apply through the existing
bounded PEKOPEKO_* override mechanism - a real process env var still wins
over a .env value, and a missing .env file is not an error.
"""
import os

import pytest

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import load_config


@pytest.fixture(autouse=True)
def _restore_real_environ():
    # python-dotenv writes straight into os.environ, bypassing monkeypatch's
    # undo tracking - snapshot/restore the whole environment so a .env value
    # loaded by one test can never leak into another.
    snapshot = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(snapshot)


def test_dotenv_value_applied_as_bounded_override(tmp_path, monkeypatch):
    monkeypatch.delenv("PEKOPEKO_OLLAMA_MODEL", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    model: file-model\n", encoding="utf-8")
    (tmp_path / ".env").write_text("PEKOPEKO_OLLAMA_MODEL=from-dotenv\n", encoding="utf-8")

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.ollama.model == "from-dotenv"


def test_real_env_var_wins_over_dotenv_value(tmp_path, monkeypatch):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    model: file-model\n", encoding="utf-8")
    (tmp_path / ".env").write_text("PEKOPEKO_OLLAMA_MODEL=from-dotenv\n", encoding="utf-8")
    monkeypatch.setenv("PEKOPEKO_OLLAMA_MODEL", "real-env")

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.ollama.model == "real-env"


def test_missing_dotenv_file_is_not_an_error(tmp_path, monkeypatch):
    monkeypatch.delenv("PEKOPEKO_OLLAMA_MODEL", raising=False)
    config_file = tmp_path / "config.yaml"
    config_file.write_text("llm_provider:\n  ollama:\n    model: file-model\n", encoding="utf-8")
    # No .env written in tmp_path.

    cfg = load_config(path=config_file)

    assert cfg.llm_provider.ollama.model == "file-model"
