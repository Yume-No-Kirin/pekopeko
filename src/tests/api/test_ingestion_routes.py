"""
Ingestion route tests: AC1 (async job contract, no real Ollama calls), AC2
(invalid domain rejected before any state write), AC3 (domain-scoped list),
AC4 (cross-domain task id returns 404).

TASK-009a upload route tests (AC1-5 of that ticket) further down.
"""
import io

from src.app.ingestion.pipeline import ingest_source
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


# TASK-009a: POST .../ingestions/upload - real file upload into _inbox/, reusing
# start_ingestion's own dispatch shape.

def test_upload_ingestion_valid_md_returns_202_and_dispatches_ingest_source(
    client, auth_headers, vault_root, state_dir, monkeypatch
):
    import src.app.api.routes_ingestion as routes_ingestion

    captured = {}

    def fake_run_in_background(fn, *args, **kwargs):
        captured["fn"] = fn
        captured["args"] = args

    monkeypatch.setattr(routes_ingestion, "run_in_background", fake_run_in_background)
    fake_provider = FakeIngestionProvider()
    monkeypatch.setattr(routes_ingestion, "build_configured_provider", lambda cfg: fake_provider)

    data = {"file": (io.BytesIO("# Test\n\nSome content.".encode("utf-8")), "notes.md")}
    resp = client.post("/domains/PERSONAL/ingestions/upload", data=data, headers=auth_headers)

    assert resp.status_code == 202
    body = resp.get_json()
    task_id = body["task_id"]
    assert body["status"] == "pending"

    written_files = list((vault_root / "PERSONAL" / "_inbox").glob("*.md"))
    assert len(written_files) == 1
    assert written_files[0].name == f"{task_id}-notes.md"
    assert written_files[0].read_text(encoding="utf-8") == "# Test\n\nSome content."

    assert captured["fn"] is ingest_source
    assert captured["args"] == (
        vault_root, "PERSONAL", written_files[0], fake_provider, state_dir / "ingestion", task_id
    )


def test_upload_ingestion_non_md_extension_returns_400_and_writes_nothing(client, auth_headers, vault_root):
    data = {"file": (io.BytesIO(b"not markdown"), "notes.txt")}
    resp = client.post("/domains/PERSONAL/ingestions/upload", data=data, headers=auth_headers)

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValueError"
    assert not (vault_root / "PERSONAL" / "_inbox").exists()


def test_upload_ingestion_missing_file_part_returns_400(client, auth_headers, vault_root):
    resp = client.post("/domains/PERSONAL/ingestions/upload", data={}, headers=auth_headers)

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValueError"
    assert not (vault_root / "PERSONAL" / "_inbox").exists()


def test_upload_ingestion_invalid_domain_returns_400_before_any_write(client, auth_headers, vault_root):
    data = {"file": (io.BytesIO(b"# Test"), "notes.md")}
    resp = client.post("/domains/NOT_A_DOMAIN/ingestions/upload", data=data, headers=auth_headers)

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValueError"
    assert not (vault_root / "NOT_A_DOMAIN").exists()


def test_upload_ingestion_same_filename_twice_produces_two_distinct_files(
    client, auth_headers, vault_root, monkeypatch
):
    import src.app.api.routes_ingestion as routes_ingestion

    monkeypatch.setattr(routes_ingestion, "run_in_background", lambda fn, *args, **kwargs: None)
    fake_provider = FakeIngestionProvider()
    monkeypatch.setattr(routes_ingestion, "build_configured_provider", lambda cfg: fake_provider)

    for _ in range(2):
        data = {"file": (io.BytesIO(b"# Test"), "same.md")}
        resp = client.post("/domains/PERSONAL/ingestions/upload", data=data, headers=auth_headers)
        assert resp.status_code == 202

    written_files = sorted((vault_root / "PERSONAL" / "_inbox").glob("*.md"))
    assert len(written_files) == 2
    assert written_files[0].name != written_files[1].name
