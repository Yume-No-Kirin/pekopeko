"""
UC-001 (Novel Ingestion), entity/event/relationship half - TC-UC001-E2E.
Real HTTP against a real Flask server and a real local Ollama. See
specs/tests/test-plan.md's "Test layers" section and the UC-001 finding
notes below - both verified empirically against a real server+Ollama in
this session (not just read from source), then written up as regression
guards here so they don't silently regress or silently get "fixed" without
Cleo noticing the review-queue behavior changed.

Finding 1 (review-queue visibility): GET /domains/<domain>/proposals never
lists an extraction-produced (entity/event/relationship) proposal, even
though the extraction task itself completes successfully and its
TaskState.proposal_ids correctly lists them. review.list_proposals()
silently `continue`s past any proposal whose frontmatter fails its
REQUIRED_PROPOSAL_FIELDS check (id/type) instead of raising - and
extraction/storage.py (TASK-003's own contract) never writes an `id` or
`type` field (it writes `item_type`, no top-level id). So today's review
queue (UC-011) is silently blind to every entity/event/relationship
proposal that exists on disk - not a 4xx anywhere, just an empty list.

Finding 2 (accept/get status code): GET or POST .../accept on one of those
proposal_ids individually returns HTTP 400 (error.type == "ValidationError"),
NOT 422 ("UnsupportedProposalTypeError") as TASK-007's own AC10/
test_review_routes.py::test_accept_entity_proposal_returns_422 asserts. That
existing test constructs its entity proposal via api/conftest.py's
make_proposal_file fixture, which writes the ingestion/review contract's
field names (id/type present) - not extraction/storage.py's real,
deliberately different contract. A proposal shaped the way extraction/
actually writes it fails review/'s own required-field validation before the
proposed_item_type business rule is ever reached.

Both are flagged here for Cleo; not fixed (out of this task's scope) -
TASK-005 will need to reconcile the two contracts, not just add business
logic.
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


def test_extraction_proposals_are_invisible_to_the_review_queue_endpoint(live_server, auth_headers, source_file):
    """Finding 1, deterministic despite real LLM content: whatever the
    provider extracted (>=1 proposal, proven via the task's own
    proposal_ids), the list endpoint reports none of it."""
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
    listed_ids = {p["id"] for p in list_resp.json()}
    assert listed_ids.isdisjoint(final["proposal_ids"])  # none of the real ones are listed


def test_extraction_proposal_get_and_accept_fail_with_validation_error(live_server, auth_headers, source_file):
    """Finding 2."""
    start_resp = requests.post(
        f"{live_server}/domains/FICTION/extractions",
        json={"source_path": str(source_file)},
        headers=auth_headers,
        timeout=10,
    )
    task_id = start_resp.json()["task_id"]
    final = poll_task_until_terminal(live_server, auth_headers, "FICTION", "extractions", task_id)
    proposal_id = final["proposal_ids"][0]

    get_resp = requests.get(f"{live_server}/domains/FICTION/proposals/{proposal_id}", headers=auth_headers, timeout=10)
    assert get_resp.status_code == 400
    assert get_resp.json()["error"]["type"] == "ValidationError"

    accept_resp = requests.post(
        f"{live_server}/domains/FICTION/proposals/{proposal_id}/accept",
        json={"reviewer_id": "cleo-e2e"},
        headers=auth_headers,
        timeout=10,
    )
    assert accept_resp.status_code == 400
    assert accept_resp.json()["error"]["type"] == "ValidationError"
