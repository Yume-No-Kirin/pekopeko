"""
Real end-to-end fixtures for src/tests/e2e/: a genuine Flask server (not
test_client()) served over a real TCP socket on 127.0.0.1, driven with real
HTTP requests and a real local Ollama - see specs/tests/test-plan.md's
"Test layers" section for why this layer exists alongside the deterministic
src/tests/acceptance/ layer, and why it can only assert structure, not exact
LLM content.

Self-contained, not shared with src/tests/api/conftest.py, matching this
project's established per-directory test-helper isolation convention.
"""
import sys
import threading
import time
from pathlib import Path

import pytest
import requests
from werkzeug.serving import make_server

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.app.api import ApiSettings, create_app  # noqa: E402
from src.app.config.loader import load_config  # noqa: E402

API_KEY = "e2e-test-api-key"


def _ollama_base_url() -> str:
    return load_config().llm_provider.ollama.base_url


@pytest.fixture(scope="session")
def ollama_reachable():
    """Gate for the whole src/tests/e2e/ layer: skips with a clear reason if
    the configured Ollama isn't reachable, rather than failing red - so
    environments without a local Ollama (e.g. one only running the
    externalized qwen3-coder setup, per AGENTS.md) still get a clean run of
    everything else."""
    base_url = _ollama_base_url()
    try:
        requests.get(base_url, timeout=2)
    except requests.exceptions.RequestException as exc:
        pytest.skip(
            f"Ollama not reachable at {base_url} ({exc}) - skipping src/tests/e2e/ "
            f"(real-server layer, opt-in via `pytest -m e2e`). Start Ollama locally "
            f"to run these; the deterministic src/tests/acceptance/ layer does not "
            f"need it and always runs."
        )
    return base_url


@pytest.fixture
def vault_root(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def live_server(vault_root, tmp_path, monkeypatch, ollama_reachable):
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(tmp_path / "task_state"))
    settings = ApiSettings(vault_root=vault_root, api_key=API_KEY)
    app = create_app(settings)

    server = make_server("127.0.0.1", 0, app)  # port 0 = OS-assigned free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{server.server_port}"
    _wait_for_server(base_url)

    yield base_url

    server.shutdown()
    thread.join(timeout=5)


def _wait_for_server(base_url: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            requests.get(f"{base_url}/config", headers={"X-API-Key": API_KEY}, timeout=1)
            return
        except requests.exceptions.RequestException:
            time.sleep(0.05)
    raise RuntimeError(f"Live e2e server did not become reachable at {base_url} within {timeout}s")


@pytest.fixture
def auth_headers():
    return {"X-API-Key": API_KEY}


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "source.md"
    path.write_text(
        "Alex traveled to the capital city in early spring. Bob was waiting at the gate.",
        encoding="utf-8",
    )
    return path
