"""
Pagination tests for the three list endpoints (TASK-007a), AC1-8.
AC1-5 are written once via `_make_items`/`_list` and parametrized over the
three endpoint kinds for AC6; AC7/AC8 are their own tests.
"""
import pytest

ENDPOINT_KINDS = ["ingestions", "extractions", "proposals"]


def _timestamp(i: int) -> str:
    # Distinct, lexicographically-and-chronologically-ordered ISO 8601 timestamps.
    return f"2026-08-{10 + i:02d}T10:00:00"


def _make_items(kind, request, n, domain="PERSONAL", status=None):
    """Creates n items of the given kind with distinct, increasing timestamps
    (item i is older than item i+1) and returns their ids in creation order."""
    ids = []
    if kind == "ingestions":
        make = request.getfixturevalue("make_ingestion_task_state")
        for i in range(n):
            ids.append(make(domain=domain, started_at=_timestamp(i), status=status or "completed"))
    elif kind == "extractions":
        make = request.getfixturevalue("make_extraction_task_state")
        for i in range(n):
            ids.append(make(domain=domain, started_at=_timestamp(i), status=status or "completed"))
    else:
        make = request.getfixturevalue("make_proposal_file")
        for i in range(n):
            proposal_id, _ = make(domain=domain, created_at=_timestamp(i), status=status or "PROPOSED")
            ids.append(proposal_id)
    return ids


def _list(client, auth_headers, kind, domain="PERSONAL", query=""):
    return client.get(f"/domains/{domain}/{kind}{query}", headers=auth_headers)


def _item_id(kind, item):
    return item["task_id"] if kind in ("ingestions", "extractions") else item["id"]


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
def test_limit_and_offset_return_exact_page(client, auth_headers, request, kind):
    _make_items(kind, request, 5)

    resp = _list(client, auth_headers, kind, query="?limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 0


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
def test_second_page_has_no_overlap_or_gap(client, auth_headers, request, kind):
    _make_items(kind, request, 5)

    page0 = _list(client, auth_headers, kind, query="?limit=2&offset=0").get_json()
    page1 = _list(client, auth_headers, kind, query="?limit=2&offset=2").get_json()

    ids0 = [_item_id(kind, i) for i in page0["items"]]
    ids1 = [_item_id(kind, i) for i in page1["items"]]
    assert len(ids1) == 2
    assert set(ids0).isdisjoint(ids1)


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
def test_defaults_applied_when_omitted(client, auth_headers, request, kind):
    _make_items(kind, request, 3)

    resp = _list(client, auth_headers, kind)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 3
    assert len(body["items"]) == 3


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
@pytest.mark.parametrize("query", ["?limit=0", "?limit=501", "?offset=-1", "?limit=abc", "?offset=abc"])
def test_invalid_pagination_params_return_400(client, auth_headers, request, kind, query):
    _make_items(kind, request, 1)

    resp = _list(client, auth_headers, kind, query=query)
    assert resp.status_code == 400
    assert resp.get_json()["error"]["type"] == "ValidationError"


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
def test_pagination_applied_after_status_filter(client, auth_headers, request, kind):
    status_a, status_b = ("completed", "failed") if kind != "proposals" else ("PROPOSED", "REJECTED")
    _make_items(kind, request, 3, status=status_a)
    _make_items(kind, request, 2, status=status_b)

    resp = _list(client, auth_headers, kind, query=f"?status={status_b}&limit=10")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


@pytest.mark.parametrize("kind", ENDPOINT_KINDS)
def test_sort_order_is_most_recent_first(client, auth_headers, request, kind):
    ids = _make_items(kind, request, 4)  # ids[0] oldest ... ids[3] most recent

    resp = _list(client, auth_headers, kind, query="?limit=10")
    body = resp.get_json()
    returned_ids = [_item_id(kind, i) for i in body["items"]]
    assert returned_ids == list(reversed(ids))


def test_single_item_and_config_endpoints_unaffected(client, auth_headers, make_proposal_file):
    """AC8 regression: single-item proposal GET and GET /config keep their
    pre-existing, non-paginated shapes untouched by this ticket."""
    proposal_id, _ = make_proposal_file(status="PROPOSED")

    detail = client.get(f"/domains/PERSONAL/proposals/{proposal_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert "items" not in detail.get_json()

    config = client.get("/config", headers=auth_headers)
    assert config.status_code == 200
    assert "items" not in config.get_json()
