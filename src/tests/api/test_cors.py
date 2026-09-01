"""
AC16: responses carry a CORS header allowing a different localhost origin
to read them, on at least one GET and one POST.
"""


def test_cors_header_present_on_get(client, auth_headers):
    resp = client.get("/config", headers=auth_headers)
    assert resp.headers.get("Access-Control-Allow-Origin") is not None


def test_cors_header_present_on_post(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="PROPOSED")
    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/reject",
        json={"reviewer_id": "r1"},
        headers=auth_headers,
    )
    assert resp.headers.get("Access-Control-Allow-Origin") is not None
