"""
Extraction route tests (AC5): identical shape to test_ingestion_routes.py,
kept separate per this project's module-independence convention.
"""
from src.app.extraction.providers.base import ExtractedEntity, ExtractionResult

from _helpers import FakeExtractionProvider, wait_for_terminal_status


def test_start_extraction_returns_202_and_eventually_completes(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeExtractionProvider(
        result=ExtractionResult(entities=[
            ExtractedEntity(local_id="e1", entity_type="person", text="Ada Lovelace", epistemic_status="direct"),
        ])
    )
    import src.app.api.routes_extraction as routes_extraction
    monkeypatch.setattr(routes_extraction, "build_configured_provider", lambda cfg: fake)

    resp = client.post(
        "/domains/PERSONAL/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    task_id = resp.get_json()["task_id"]

    immediate = client.get(f"/domains/PERSONAL/extractions/{task_id}", headers=auth_headers)
    assert immediate.status_code == 200

    final = wait_for_terminal_status(state_dir, task_id, "extraction")
    assert final["status"] == "completed"
    assert final["source_id"] is not None
    assert len(final["proposal_ids"]) == 1
    assert fake.calls == 1


def test_start_extraction_invalid_domain_returns_400_before_any_write(client, auth_headers, source_file, state_dir):
    resp = client.post(
        "/domains/NOT_A_DOMAIN/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["type"] == "InvalidDomainError"

    extraction_state_dir = state_dir / "extraction"
    assert not extraction_state_dir.exists() or list(extraction_state_dir.glob("*.json")) == []


def test_start_extraction_missing_source_path_returns_400(client, auth_headers):
    resp = client.post("/domains/PERSONAL/extractions", json={}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValueError"


def test_get_extraction_invalid_domain_returns_400(client, auth_headers):
    resp = client.get("/domains/NOPE/extractions/extract-x", headers=auth_headers)
    assert resp.status_code == 400


def test_list_extractions_invalid_domain_returns_400(client, auth_headers):
    resp = client.get("/domains/NOPE/extractions", headers=auth_headers)
    assert resp.status_code == 400


def test_list_extractions_scoped_to_domain(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeExtractionProvider(result=ExtractionResult())
    import src.app.api.routes_extraction as routes_extraction
    monkeypatch.setattr(routes_extraction, "build_configured_provider", lambda cfg: fake)

    resp_personal = client.post(
        "/domains/PERSONAL/extractions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id_personal = resp_personal.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id_personal, "extraction")

    resp_fiction = client.post(
        "/domains/FICTION/extractions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id_fiction = resp_fiction.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id_fiction, "extraction")

    listed = client.get("/domains/PERSONAL/extractions", headers=auth_headers)
    assert listed.status_code == 200
    ids = [t["task_id"] for t in listed.get_json()["items"]]
    assert task_id_personal in ids
    assert task_id_fiction not in ids


def test_get_extraction_wrong_domain_returns_404(client, auth_headers, source_file, state_dir, monkeypatch):
    fake = FakeExtractionProvider(result=ExtractionResult())
    import src.app.api.routes_extraction as routes_extraction
    monkeypatch.setattr(routes_extraction, "build_configured_provider", lambda cfg: fake)

    resp = client.post(
        "/domains/PERSONAL/extractions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    task_id = resp.get_json()["task_id"]
    wait_for_terminal_status(state_dir, task_id, "extraction")

    cross_domain = client.get(f"/domains/FICTION/extractions/{task_id}", headers=auth_headers)
    assert cross_domain.status_code == 404
