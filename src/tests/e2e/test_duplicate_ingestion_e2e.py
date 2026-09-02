"""
UC-016 (Duplicate/Repeated Ingestion) - TC-UC016-E2E. Real HTTP against a
real Flask server and a real local Ollama.

Unlike the other e2e tests, this one is fully exact-value deterministic
even with a real LLM: duplicate detection (INV-020) short-circuits before
the provider is ever called, so the second call's outcome never depends on
LLM content.
"""
import pytest
import requests
from _e2e_helpers import poll_task_until_terminal

pytestmark = pytest.mark.e2e


def test_duplicate_ingestion_via_real_server_reaches_skipped_duplicate(live_server, auth_headers, source_file):
    first_resp = requests.post(
        f"{live_server}/domains/PERSONAL/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    assert first_resp.status_code == 202
    first_task_id = first_resp.json()["task_id"]
    first_final = poll_task_until_terminal(live_server, auth_headers, "PERSONAL", "ingestions", first_task_id)
    assert first_final["status"] == "completed", first_final.get("error")

    second_resp = requests.post(
        f"{live_server}/domains/PERSONAL/ingestions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    assert second_resp.status_code == 202
    second_task_id = second_resp.json()["task_id"]
    second_final = poll_task_until_terminal(live_server, auth_headers, "PERSONAL", "ingestions", second_task_id)

    assert second_final["status"] == "skipped_duplicate"
    assert second_final["source_id"] == first_final["source_id"]
