"""
AC1: with no config file present and no relevant environment variable set,
load_config() returns the documented built-in defaults and never raises.
"""
from _helpers import REPO_ROOT

from src.app.config import load_config


def test_defaults_when_no_file_and_no_env(tmp_path, monkeypatch):
    for var in (
        "PEKOPEKO_CONFIG_PATH",
        "PEKOPEKO_LLM_PROVIDER",
        "PEKOPEKO_OLLAMA_BASE_URL",
        "PEKOPEKO_OLLAMA_MODEL",
        "PEKOPEKO_OLLAMA_TIMEOUT",
        "PEKOPEKO_OLLAMA_TEMPERATURE",
        "PEKOPEKO_TASK_STATE_DIR",
        "PEKOPEKO_RETRIEVAL_INDEX_DIR",
    ):
        monkeypatch.delenv(var, raising=False)

    missing_path = tmp_path / "does_not_exist.yaml"
    cfg = load_config(path=missing_path)

    assert cfg.llm_provider.active == "ollama"
    assert cfg.llm_provider.ollama.base_url == "http://localhost:11434"
    assert cfg.llm_provider.ollama.model == "llama3"
    assert cfg.llm_provider.ollama.timeout == 60
    assert cfg.llm_provider.ollama.temperature == 0.7
    assert cfg.retrieval.index_dir == REPO_ROOT / ".pekopeko" / "retrieval_index"
    assert cfg.task_state.dir == REPO_ROOT / ".pekopeko" / "task_state"
