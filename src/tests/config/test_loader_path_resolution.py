"""
AC3: PEKOPEKO_CONFIG_PATH makes load_config() read from that exact path
instead of the default ~/.pekopeko/config.yaml; a missing file at that
explicit path is treated as "no file" (defaults), not an error.
"""
from pathlib import Path

from _helpers import REPO_ROOT  # noqa: F401

from src.app.config import load_config


def test_env_config_path_is_used_when_no_explicit_path_given(tmp_path, monkeypatch):
    config_file = tmp_path / "somewhere" / "config.yaml"
    config_file.parent.mkdir()
    config_file.write_text("llm_provider:\n  ollama:\n    model: phi3\n", encoding="utf-8")

    monkeypatch.setenv("PEKOPEKO_CONFIG_PATH", str(config_file))

    cfg = load_config()

    assert cfg.llm_provider.ollama.model == "phi3"


def test_missing_file_at_env_config_path_is_treated_as_no_file(tmp_path, monkeypatch):
    missing_path = tmp_path / "nope" / "config.yaml"
    monkeypatch.setenv("PEKOPEKO_CONFIG_PATH", str(missing_path))

    cfg = load_config()  # must not raise

    assert cfg.llm_provider.active == "ollama"
    assert cfg.llm_provider.ollama.model == "llama3"


def test_default_path_used_when_no_arg_and_no_env_var(tmp_path, monkeypatch):
    # Never touch the real home directory: monkeypatch Path.home() to a
    # tmp_path so the ~/.pekopeko/config.yaml default resolves under it
    # (and predictably doesn't exist there, so defaults are returned).
    monkeypatch.delenv("PEKOPEKO_CONFIG_PATH", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    cfg = load_config()

    assert cfg.llm_provider.active == "ollama"
    assert cfg.task_state.dir == tmp_path / ".pekopeko" / "task_state"


def test_explicit_path_argument_wins_over_env_var(tmp_path, monkeypatch):
    env_config_file = tmp_path / "from_env.yaml"
    env_config_file.write_text("llm_provider:\n  ollama:\n    model: from-env\n", encoding="utf-8")
    monkeypatch.setenv("PEKOPEKO_CONFIG_PATH", str(env_config_file))

    explicit_config_file = tmp_path / "from_arg.yaml"
    explicit_config_file.write_text("llm_provider:\n  ollama:\n    model: from-arg\n", encoding="utf-8")

    cfg = load_config(path=explicit_config_file)

    assert cfg.llm_provider.ollama.model == "from-arg"
