"""
UC-001 (Novel Ingestion), assertion flow - TC-UC001-E2E. Real HTTP POST
against a real Flask server, calling a real local Ollama, polled to
completion, then accepted through the real API. See
specs/tests/test-plan.md's "Test layers" section: content produced by the
real LLM varies between runs, so only structure/contract is asserted here
(status codes, required fields, valid enum membership, file existence). The
exact same guarantees with precise, reproducible content assertions live in
src/tests/acceptance/test_ingestion_to_review_end_to_end.py.
"""
import pytest
import requests
from _e2e_helpers import poll_task_until_terminal

pytestmark = pytest.mark.e2e

VALID_EPISTEMIC_STATUSES = {"direct", "inferred", "uncertain", "contested"}


def test_ingestion_round_trip_via_real_server_and_ollama(live_server, auth_headers, source_file, vault_root):
    start_resp = requests.post(
        f"{live_server}/domains/FICTION/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    assert start_resp.status_code == 202
    task_id = start_resp.json()["task_id"]
    assert task_id

    final = poll_task_until_terminal(live_server, auth_headers, "FICTION", "ingestions", task_id)
    assert final["status"] == "completed", final.get("error")
    assert final["source_id"]
    assert len(final["proposal_ids"]) >= 1

    proposals_resp = requests.get(f"{live_server}/domains/FICTION/proposals", headers=auth_headers, timeout=10)
    assert proposals_resp.status_code == 200
    proposals = proposals_resp.json()
    assert len(proposals) >= 1
    for p in proposals:
        assert p["epistemic_status"] in VALID_EPISTEMIC_STATUSES
        assert p["proposal_status"] == "PROPOSED"
        assert p["proposed_item_type"] == "assertion"

    accept_resp = requests.post(
        f"{live_server}/domains/FICTION/proposals/{proposals[0]['id']}/accept",
        json={"reviewer_id": "cleo-e2e"},
        headers=auth_headers,
        timeout=10,
    )
    assert accept_resp.status_code == 200
    assertion_id = accept_resp.json()["assertion_id"]
    canonical_path = vault_root / "FICTION" / "assertions" / assertion_id / f"{assertion_id}.md"
    assert canonical_path.exists()
