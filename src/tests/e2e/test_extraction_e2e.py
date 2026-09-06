"""
UC-001 (Novel Ingestion), entity/event/relationship half - TC-UC001-E2E.
Real HTTP against a real Flask server and a real local Ollama. See
specs/tests/test-plan.md's "Test layers" section.

Until TASK-003a + TASK-005, two real gaps existed here (see
specs/tasks/backlog/TASK-005-entity-event-relationship-review.md's
Implementation notes for the full history): extraction-produced proposals
were invisible to GET /domains/<domain>/proposals, and GET/accept on one
individually returned 400 ValidationError rather than ever reaching the
proposed_item_type business rule. Both are fixed now - these tests assert
the corrected behavior as regression guards.

Not re-run in this session (no live Ollama available here) - flagged
`[NOT RUN]` in TASK-005's own verification record, same as every other
e2e-marked test in prior tickets' verification records.
"""
import pytest
import requests
from _e2e_helpers import poll_task_until_terminal

pytestmark = pytest.mark.e2e

VALID_EPISTEMIC_STATUSES = {"direct", "inferred", "uncertain", "contested"}


def test_extraction_completes_and_creates_proposals_on_disk(live_server, auth_headers, source_file):
    start_resp = requests.post(
        f"{live_server}/domains/FICTION/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    assert start_resp.status_code == 202
    task_id = start_resp.json()["task_id"]

    final = poll_task_until_terminal(live_server, auth_headers, "FICTION", "extractions", task_id)
    assert final["status"] == "completed", final.get("error")
    assert len(final["proposal_ids"]) >= 1


def test_extraction_proposals_are_visible_to_the_review_queue_endpoint(live_server, auth_headers, source_file):
    """Deterministic despite real LLM content: whatever the provider
    extracted (>=1 proposal, proven via the task's own proposal_ids), the
    list endpoint now reports all of it (TASK-003a's id/type fields)."""
    start_resp = requests.post(
        f"{live_server}/domains/FICTION/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    task_id = start_resp.json()["task_id"]
    final = poll_task_until_terminal(live_server, auth_headers, "FICTION", "extractions", task_id)
    assert len(final["proposal_ids"]) >= 1  # they really exist on disk

    list_resp = requests.get(f"{live_server}/domains/FICTION/proposals", headers=auth_headers, timeout=10)
    assert list_resp.status_code == 200
    listed_ids = {p["id"] for p in list_resp.json()["items"]}
    assert set(final["proposal_ids"]).issubset(listed_ids)


def test_extraction_entity_proposal_get_and_accept_succeed(live_server, auth_headers, source_file):
    """GET and accept now succeed for a real extraction-produced proposal
    (TASK-005). Picks an `entity` proposal specifically (rather than
    proposal_ids[0]) so the test is deterministic regardless of real LLM
    output order/mix: an entity never has unresolved-endpoint preconditions,
    unlike a relationship (covered at the unit/acceptance layer instead,
    where fixture content is controlled)."""
    start_resp = requests.post(
        f"{live_server}/domains/FICTION/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    task_id = start_resp.json()["task_id"]
    final = poll_task_until_terminal(live_server, auth_headers, "FICTION", "extractions", task_id)

    entity_proposal_id = None
    for proposal_id in final["proposal_ids"]:
        detail_resp = requests.get(
            f"{live_server}/domains/FICTION/proposals/{proposal_id}", headers=auth_headers, timeout=10
        )
        assert detail_resp.status_code == 200
        if detail_resp.json()["frontmatter"]["proposed_item_type"] == "entity":
            entity_proposal_id = proposal_id
            break
    assert entity_proposal_id is not None, "expected at least one entity proposal"

    accept_resp = requests.post(
        f"{live_server}/domains/FICTION/proposals/{entity_proposal_id}/accept",
        json={"reviewer_id": "cleo-e2e"},
        headers=auth_headers,
        timeout=10,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["assertion_id"].startswith("entity-")
