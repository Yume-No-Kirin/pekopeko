"""
AC13: a request with a missing or wrong X-API-Key header returns 401 for
every route, before any domain/business logic runs (an invalid domain in
the same request must not produce a 400 instead).
"""
import pytest

ROUTES = [
    ("GET", "/domains/PERSONAL/ingestions"),
    ("POST", "/domains/PERSONAL/ingestions"),
    ("GET", "/domains/PERSONAL/ingestions/ingest-x"),
    ("GET", "/domains/PERSONAL/extractions"),
    ("POST", "/domains/PERSONAL/extractions"),
    ("GET", "/domains/PERSONAL/proposals"),
    ("GET", "/domains/PERSONAL/proposals/prop-x"),
    ("POST", "/domains/PERSONAL/proposals/prop-x/accept"),
    ("POST", "/domains/PERSONAL/proposals/prop-x/reject"),
    ("GET", "/config"),
]


@pytest.mark.parametrize("method,path", ROUTES)
def test_missing_api_key_returns_401(client, method, path):
    resp = client.open(path, method=method, json={})
    assert resp.status_code == 401
    assert resp.get_json()["error"]["type"] == "Unauthorized"


@pytest.mark.parametrize("method,path", ROUTES)
def test_wrong_api_key_returns_401(client, method, path):
    resp = client.open(path, method=method, json={}, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_missing_api_key_on_invalid_domain_still_401_not_400(client):
    """A bad domain in the URL must not leak a 400 before the 401 auth check."""
    resp = client.get("/domains/NOT_A_DOMAIN/ingestions")
    assert resp.status_code == 401
