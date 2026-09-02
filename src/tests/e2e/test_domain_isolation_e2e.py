"""
UC-009 (Cross-Domain Analysis, isolation slice) and UC-018 (Fictional
Universe Isolation, domain-level slice) - TC-UC009-E2E. Real HTTP against a
real Flask server and a real local Ollama.

Deterministic regardless of LLM content: these assertions are about routing/
isolation (task_id and proposal_id 404s across domains), not about what the
LLM actually extracted.
"""
import pytest
import requests
from _e2e_helpers import poll_task_until_terminal

pytestmark = pytest.mark.e2e


def test_ingestion_task_is_not_found_under_a_different_domain(live_server, auth_headers, source_file):
    start_resp = requests.post(
        f"{live_server}/domains/PERSONAL/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    assert start_resp.status_code == 202
    task_id = start_resp.json()["task_id"]
    poll_task_until_terminal(live_server, auth_headers, "PERSONAL", "ingestions", task_id)

    same_domain_resp = requests.get(
        f"{live_server}/domains/PERSONAL/ingestions/{task_id}", headers=auth_headers, timeout=10
    )
    assert same_domain_resp.status_code == 200

    cross_domain_resp = requests.get(
        f"{live_server}/domains/FICTION/ingestions/{task_id}", headers=auth_headers, timeout=10
    )
    assert cross_domain_resp.status_code == 404


def test_proposal_is_not_found_under_a_different_domain(live_server, auth_headers, source_file):
    start_resp = requests.post(
        f"{live_server}/domains/PERSONAL/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    task_id = start_resp.json()["task_id"]
    final = poll_task_until_terminal(live_server, auth_headers, "PERSONAL", "ingestions", task_id)
    proposal_id = final["proposal_ids"][0]

    cross_domain_resp = requests.get(
        f"{live_server}/domains/FICTION/proposals/{proposal_id}", headers=auth_headers, timeout=10
    )
    assert cross_domain_resp.status_code == 404
    assert cross_domain_resp.json()["error"]["type"] == "ProposalNotFoundError"
