"""
Review route tests: AC6 (list/filter matches review.list_proposals),
AC7 (missing proposal 404), AC8 (accept happy path, pure pass-through),
AC9 (accept on non-PROPOSED -> 409), AC10 (accept on entity/event/
relationship -> 200, since TASK-005 - see that ticket for the superseded
original AC10; the relationship case is TASK-012's own AC12),
AC11 (reject with reason -> 200, rejection_reason set).

TASK-013 edit route tests (AC1-8 of that ticket): success path, missing
reviewer_id, disallowed field_updates key, non-PROPOSED/EDITED status,
domain mismatch, empty body+field_updates.
"""
from pathlib import Path


def test_list_proposals_matches_and_filters_by_status(client, auth_headers, make_proposal_file):
    id_proposed, _ = make_proposal_file(status="PROPOSED")
    id_rejected, _ = make_proposal_file(status="REJECTED")

    resp = client.get("/domains/PERSONAL/proposals", headers=auth_headers)
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.get_json()["items"]]
    assert id_proposed in ids
    assert id_rejected in ids

    filtered = client.get("/domains/PERSONAL/proposals?status=PROPOSED", headers=auth_headers)
    filtered_ids = [p["id"] for p in filtered.get_json()["items"]]
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


def test_accept_entity_proposal_returns_200(client, auth_headers, make_proposal_file):
    # TASK-005 supersedes TASK-007's original AC10 (422 for non-assertion
    # accept) - entity/event/relationship proposals are now acceptable.
    proposal_id, _ = make_proposal_file(
        status="PROPOSED", proposed_item_type="entity", entity_type="person"
    )

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["assertion_id"].startswith("entity-")


def test_accept_event_proposal_returns_200(client, auth_headers, make_proposal_file):
    # TASK-012 AC12: event accept succeeds, carrying starts_at/ends_at.
    proposal_id, _ = make_proposal_file(
        status="PROPOSED", proposed_item_type="event", starts_at="2026-08-01T10:00:00", ends_at=None
    )

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["assertion_id"].startswith("event-")


def test_accept_relationship_proposal_returns_200(client, auth_headers, make_proposal_file):
    # TASK-012 AC12: relationship accept succeeds once every endpoint is
    # already resolvable (an ACCEPTED proposal's resulting_item_id, or a
    # passthrough id matching no proposal at all).
    endpoint_id, _ = make_proposal_file(status="PROPOSED", proposed_item_type="entity", entity_type="person")
    client.post(
        f"/domains/PERSONAL/proposals/{endpoint_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    proposal_id, _ = make_proposal_file(
        status="PROPOSED",
        proposed_item_type="relationship",
        relationship_type="attended",
        endpoints=[endpoint_id, "some-existing-canonical-id"],
    )

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["assertion_id"].startswith("relationship-")


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


def test_edit_proposed_assertion_returns_200_and_updates_file(client, auth_headers, make_proposal_file):
    proposal_id, path = make_proposal_file(status="PROPOSED", body="Original text.")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={
            "reviewer_id": "reviewer-1",
            "body": "Edited text.",
            "field_updates": {
                "epistemic_status": "inferred",
                "valid_from": "2026-09-01T00:00:00",
                "valid_until": "2026-12-31T00:00:00",
            },
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["proposal_id"] == proposal_id
    assert body["edited_by"] == "reviewer-1"
    assert "edited_at" in body
    assert body["archived_version"] == 1
    assert Path(body["archived_version_path"]).exists()

    detail = client.get(f"/domains/PERSONAL/proposals/{proposal_id}", headers=auth_headers).get_json()
    assert detail["body"] == "Edited text."
    assert detail["frontmatter"]["proposal_status"] == "EDITED"
    assert detail["frontmatter"]["epistemic_status"] == "inferred"
    assert detail["frontmatter"]["valid_from"] == "2026-09-01T00:00:00"
    assert detail["frontmatter"]["valid_until"] == "2026-12-31T00:00:00"
    assert detail["frontmatter"]["edited_by"] == "reviewer-1"
    assert "edited_at" in detail["frontmatter"]


def test_edit_missing_reviewer_id_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={"body": "Edited text."},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_edit_disallowed_field_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={"reviewer_id": "reviewer-1", "field_updates": {"id": "some-other-id"}},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "UneditableFieldError"


def test_edit_non_proposed_or_edited_returns_409(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="ACCEPTED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={"reviewer_id": "reviewer-1", "body": "Edited text."},
        headers=auth_headers,
    )
    assert resp.status_code == 409
    assert resp.get_json()["error"]["type"] == "InvalidProposalStatusError"


def test_edit_domain_mismatch_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED", internal_domain="FICTION")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={"reviewer_id": "reviewer-1", "body": "Edited text."},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "DomainMismatchError"


def test_edit_empty_body_and_field_updates_returns_400(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/edit",
        json={"reviewer_id": "reviewer-1"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


# TASK-014: GET .../organization-folders (assertion-only)

def test_get_organization_folders_empty_domain_returns_empty_structure(client, auth_headers):
    resp = client.get("/domains/PERSONAL/organization-folders?item_type=assertion", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.get_json() == {"segments_by_depth": []}


def test_get_organization_folders_multi_depth_scan(client, auth_headers, vault_root):
    assertions_dir = vault_root / "PERSONAL" / "assertions"
    (assertions_dir / "mythologie" / "japonaise" / "assert-1").mkdir(parents=True)
    (assertions_dir / "livres" / "assert-2").mkdir(parents=True)

    resp = client.get("/domains/PERSONAL/organization-folders?item_type=assertion", headers=auth_headers)

    assert resp.status_code == 200
    assert resp.get_json() == {"segments_by_depth": [["livres", "mythologie"], ["japonaise"]]}


def test_get_organization_folders_missing_item_type_returns_400(client, auth_headers):
    resp = client.get("/domains/PERSONAL/organization-folders", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_get_organization_folders_invalid_item_type_returns_400(client, auth_headers):
    resp = client.get("/domains/PERSONAL/organization-folders?item_type=entity", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


def test_get_organization_folders_invalid_domain_returns_400(client, auth_headers):
    resp = client.get("/domains/NOT_A_DOMAIN/organization-folders?item_type=assertion", headers=auth_headers)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "InvalidDomainError"
