"""
TASK-015 batch route tests: POST .../proposals/accept-batch and
.../proposals/reject-batch. AC1 (all-succeed, one call, order preserved),
AC2 (partial failure - unresolved relationship endpoint - stays 200),
AC8 (200 even when every item fails; 400 only for a structurally invalid
request), AC9 (individual /accept, /reject unchanged - not rerouted),
AC10 (no file under src/app/review/ is touched by this ticket, verified via
git status separately, not by these tests).
"""


def test_accept_batch_all_succeed_returns_200(client, auth_headers, make_proposal_file):
    id_assertion, _ = make_proposal_file(status="PROPOSED", proposed_item_type="assertion")
    id_entity, _ = make_proposal_file(status="PROPOSED", proposed_item_type="entity", entity_type="person")

    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": [id_assertion, id_entity]},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["succeeded_count"] == 2
    assert body["failed_count"] == 0
    assert [r["proposal_id"] for r in body["results"]] == [id_assertion, id_entity]
    assert all(r["status"] == "accepted" for r in body["results"])


def test_accept_batch_partial_failure_unresolved_relationship_endpoint(client, auth_headers, make_proposal_file):
    # Endpoint proposal deliberately left PROPOSED (not accepted first, and not
    # in this same batch) - the relationship's endpoint resolution must fail.
    endpoint_id, _ = make_proposal_file(status="PROPOSED", proposed_item_type="entity", entity_type="person")
    relationship_id, _ = make_proposal_file(
        status="PROPOSED",
        proposed_item_type="relationship",
        relationship_type="attended",
        endpoints=[endpoint_id, "some-existing-canonical-id"],
    )
    assertion_id, _ = make_proposal_file(status="PROPOSED", proposed_item_type="assertion")

    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": [relationship_id, assertion_id]},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["succeeded_count"] < len(body["results"])
    assert body["failed_count"] >= 1
    results_by_id = {r["proposal_id"]: r for r in body["results"]}
    assert results_by_id[relationship_id]["status"] == "failed"
    assert results_by_id[relationship_id]["error"]["type"] == "UnresolvedRelationshipEndpointError"
    assert results_by_id[assertion_id]["status"] == "accepted"


def test_accept_batch_all_fail_still_returns_200(client, auth_headers):
    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": ["prop-does-not-exist-1", "prop-does-not-exist-2"]},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["succeeded_count"] == 0
    assert body["failed_count"] == 2
    assert all(r["status"] == "failed" for r in body["results"])
    assert all(r["error"]["type"] == "ProposalNotFoundError" for r in body["results"])


def test_accept_batch_missing_reviewer_id_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"proposal_ids": [proposal_id]},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_accept_batch_missing_proposal_ids_returns_400(client, auth_headers):
    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_accept_batch_non_list_proposal_ids_returns_400(client, auth_headers):
    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": "prop-1"},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_accept_batch_empty_proposal_ids_returns_400(client, auth_headers):
    resp = client.post(
        "/domains/PERSONAL/proposals/accept-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": []},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_reject_batch_all_succeed_shares_one_reason(client, auth_headers, make_proposal_file):
    id_1, path_1 = make_proposal_file(status="PROPOSED")
    id_2, path_2 = make_proposal_file(status="PROPOSED")

    resp = client.post(
        "/domains/PERSONAL/proposals/reject-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": [id_1, id_2], "reason": "duplicate batch"},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["succeeded_count"] == 2
    assert all(r["rejection_reason"] == "duplicate batch" for r in body["results"])
    assert "duplicate batch" in path_1.read_text(encoding="utf-8")
    assert "duplicate batch" in path_2.read_text(encoding="utf-8")


def test_reject_batch_blank_reason_sends_null_to_every_item(client, auth_headers, make_proposal_file):
    id_1, _ = make_proposal_file(status="PROPOSED")
    id_2, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        "/domains/PERSONAL/proposals/reject-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": [id_1, id_2]},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert all(r["rejection_reason"] is None for r in body["results"])


def test_reject_batch_partial_failure(client, auth_headers, make_proposal_file):
    id_1, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        "/domains/PERSONAL/proposals/reject-batch",
        json={"reviewer_id": "reviewer-1", "proposal_ids": [id_1, "prop-does-not-exist"]},
        headers=auth_headers,
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["failed_count"] == 1
    results_by_id = {r["proposal_id"]: r for r in body["results"]}
    assert results_by_id[id_1]["status"] == "rejected"
    assert results_by_id["prop-does-not-exist"]["error"]["type"] == "ProposalNotFoundError"


def test_reject_batch_missing_reviewer_id_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        "/domains/PERSONAL/proposals/reject-batch",
        json={"proposal_ids": [proposal_id]},
        headers=auth_headers,
    )

    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_individual_accept_and_reject_routes_unchanged(client, auth_headers, make_proposal_file):
    id_accept, _ = make_proposal_file(status="PROPOSED")
    id_reject, _ = make_proposal_file(status="PROPOSED")

    accept_resp = client.post(
        f"/domains/PERSONAL/proposals/{id_accept}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    reject_resp = client.post(
        f"/domains/PERSONAL/proposals/{id_reject}/reject",
        json={"reviewer_id": "reviewer-1", "reason": "nope"},
        headers=auth_headers,
    )

    assert accept_resp.status_code == 200
    assert "results" not in accept_resp.get_json()
    assert "succeeded_count" not in accept_resp.get_json()

    assert reject_resp.status_code == 200
    assert "results" not in reject_resp.get_json()
    assert "succeeded_count" not in reject_resp.get_json()
