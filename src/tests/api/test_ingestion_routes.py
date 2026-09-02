"""
Ingestion route tests: AC1 (async job contract, no real Ollama calls), AC2
(invalid domain rejected before any state write), AC3 (domain-scoped list),
AC4 (cross-domain task id returns 404).
"""
from src.app.ingestion.providers.base import ExtractedAssertion, ExtractionResult
from src.app.ingestion.task_state import load_task_state

from _helpers import FakeIngestionProvider, wait_for_terminal_status


def test_start_ingestion_returns_202_and_eventually_completes(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeIngestionProvider(
        result=ExtractionResult(assertions=[
            ExtractedAssertion(text="A fact", epistemic_status="direct"),
            ExtractedAssertion(text="Another fact", epistemic_status="inferred"),
        ])
    )
    import src.app.api.routes_ingestion as routes_ingestion
    monkeypatch.setattr(routes_ingestion, "build_configured_provider", lambda cfg: fake)

    resp = client.post(
        "/domains/PERSONAL/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    task_id = resp.get_json()["task_id"]
    assert resp.get_json()["status"] == "pending"

    # The pending state file already exists - an immediate GET never 404s.
    immediate = client.get(f"/domains/PERSONAL/ingestions/{task_id}", headers=auth_headers)
    assert immediate.status_code == 200

    final = wait_for_terminal_status(state_dir, task_id, "ingestion")
    assert final["status"] == "completed"
    assert final["source_id"] is not None
    assert len(final["proposal_ids"]) == 2
    assert fake.calls == 1


def test_start_ingestion_invalid_domain_returns_400_before_any_write(client, auth_headers, source_file, state_dir):
    resp = client.post(
        "/domains/NOT_A_DOMAIN/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["type"] == "ValueError"

    ingestion_state_dir = state_dir / "ingestion"
    assert not ingestion_state_dir.exists() or list(ingestion_state_dir.glob("*.json")) == []


def test_start_ingestion_missing_source_path_returns_400(client, auth_headers):
    resp = client.post("/domains/PERSONAL/ingestions", json={}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValueError"


def test_get_ingestion_invalid_domain_returns_400(client, auth_headers):
    resp = client.get("/domains/NOPE/ingestions/ingest-x", headers=auth_headers)
    assert resp.status_code == 400


def test_list_ingestions_invalid_domain_returns_400(client, auth_headers):
    resp = client.get("/domains/NOPE/ingestions", headers=auth_headers)
    assert resp.status_code == 400


def test_list_ingestions_scoped_to_domain(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeIngestionProvider(result=ExtractionResult(assertions=[]))
    import src.app.api.routes_ingestion as routes_ingestion
    monkeypatch.setattr(routes_ingestion, "build_configured_provider", lambda cfg: fake)

    resp_personal = client.post(
        "/domains/PERSONAL/ingestions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id_personal = resp_personal.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id_personal, "ingestion")

    resp_fiction = client.post(
        "/domains/FICTION/ingestions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id_fiction = resp_fiction.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id_fiction, "ingestion")

    listed = client.get("/domains/PERSONAL/ingestions", headers=auth_headers)
    assert listed.status_code == 200
    ids = [t["task_id"] for t in listed.get_json()["items"]]
    assert task_id_personal in ids
    assert task_id_fiction not in ids


def test_get_ingestion_wrong_domain_returns_404(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeIngestionProvider(result=ExtractionResult(assertions=[]))
    import src.app.api.routes_ingestion as routes_ingestion
    monkeypatch.setattr(routes_ingestion, "build_configured_provider", lambda cfg: fake)

    resp = client.post(
        "/domains/PERSONAL/ingestions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id = resp.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id, "ingestion")

    cross_domain = client.get(f"/domains/FICTION/ingestions/{task_id}", headers=auth_headers)
    assert cross_domain.status_code == 404
