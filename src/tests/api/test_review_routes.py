"""
Review route tests: AC6 (list/filter matches review.list_proposals),
AC7 (missing proposal 404), AC8 (accept happy path, pure pass-through),
AC9 (accept on non-PROPOSED -> 409), AC10 (accept on entity -> 422),
AC11 (reject with reason -> 200, rejection_reason set).
"""
from pathlib import Path


def test_list_proposals_matches_and_filters_by_status(client, auth_headers, make_proposal_file):
    id_proposed, _ = make_proposal_file(status="PROPOSED")
    id_rejected, _ = make_proposal_file(status="REJECTED")

    resp = client.get("/domains/PERSONAL/proposals", headers=auth_headers)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.get_json()]
    assert id_proposed in ids
    assert id_rejected in ids

    filtered = client.get("/domains/PERSONAL/proposals?status=PROPOSED", headers=auth_headers)
    filtered_ids = [p["id"] for p in filtered.get_json()]
    assert id_proposed in filtered_ids
    assert id_rejected not in filtered_ids


def test_get_proposal_detail_returns_full_body(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED", body="Full assertion body text.")

    resp = client.get(f"/domains/PERSONAL/proposals/{proposal_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["id"] == proposal_id
    assert body["body"] == "Full assertion body text."
    assert "frontmatter" in body
    assert "source_body" in body


def test_get_proposal_missing_returns_404(client, auth_headers):
    resp = client.get("/domains/PERSONAL/proposals/prop-does-not-exist", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.get_json()["error"]["type"] == "ProposalNotFoundError"


def test_accept_proposed_assertion_returns_200_and_writes_canonical_file(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["proposal_id"] == proposal_id
    assert body["reviewed_by"] == "reviewer-1"
    assert Path(body["assertion_path"]).exists()


def test_accept_non_proposed_returns_409(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="ACCEPTED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"]["type"] == "InvalidProposalStatusError"


def test_accept_entity_proposal_returns_422(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(
        status="PROPOSED", proposed_item_type="entity", entity_type="person"
    )

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert resp.get_json()["error"]["type"] == "UnsupportedProposalTypeError"


def test_reject_with_reason_returns_200_and_sets_rejection_reason(client, auth_headers, make_proposal_file):
    proposal_id, path = make_proposal_file(status="PROPOSED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/reject",
        json={"reviewer_id": "reviewer-1", "reason": "duplicate of an existing fact"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["rejection_reason"] == "duplicate of an existing fact"
    assert "duplicate of an existing fact" in path.read_text(encoding="utf-8")
