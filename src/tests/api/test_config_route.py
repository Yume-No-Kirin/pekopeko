"""
AC12: GET /config returns the required fields, Path fields as strings;
no write endpoint exists.
"""


def test_get_config_returns_required_fields(client, auth_headers):
    resp = client.get("/config", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "active" in body["llm_provider"]
    assert isinstance(body["retrieval"]["index_dir"], str)
    assert isinstance(body["task_state"]["dir"], str)
    assert "domain" in body["default"]


def test_no_config_write_endpoint(client, auth_headers):
    resp = client.post("/config", json={}, headers=auth_headers)
    assert resp.status_code in (404, 405)
