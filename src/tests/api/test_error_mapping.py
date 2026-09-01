"""
AC15: every non-2xx response follows {"error": {"type": ..., "message": ...}},
with at least one case per row of TASK-007's Error mapping table. Naturally
HTTP-reachable rows are exercised end-to-end; rows that ingest_source/
extract_source swallow internally rather than ever raise synchronously
(ExtractionValidationError, ReviewValidationError, ConfigError) are
exercised via a throwaway route added to the app under test, to verify the
Flask error-handler wiring itself maps them correctly.
"""
from src.app.api.app import ERROR_STATUS_MAP
from src.app.config.errors import ConfigError
from src.app.extraction.errors import ValidationError as ExtractionValidationError
from src.app.review.errors import ValidationError as ReviewValidationError


def _assert_envelope(resp, expected_status, expected_type):
    assert resp.status_code == expected_status
    body = resp.get_json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"type", "message"}
    assert body["error"]["type"] == expected_type


def test_error_status_map_covers_every_ticket_row():
    statuses_by_name = {cls.__name__: status for cls, status in ERROR_STATUS_MAP.items()}
    assert statuses_by_name["ValueError"] == 400
    assert statuses_by_name["InvalidDomainError"] == 400  # both extraction/review variants share this name
    assert statuses_by_name["ValidationError"] == 400  # both extraction/review variants share this name
    assert statuses_by_name["ProposalNotFoundError"] == 404
    assert statuses_by_name["SourceNotFoundError"] == 404
    assert statuses_by_name["DomainMismatchError"] == 400
    assert statuses_by_name["InvalidProposalStatusError"] == 409
    assert statuses_by_name["UnsupportedProposalTypeError"] == 422
    assert statuses_by_name["ConfigError"] == 500


def test_ingestion_bad_domain_maps_to_400_value_error(client, auth_headers, source_file):
    resp = client.post(
        "/domains/NOPE/ingestions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    _assert_envelope(resp, 400, "ValueError")


def test_extraction_bad_domain_maps_to_400_invalid_domain_error(client, auth_headers, source_file):
    resp = client.post(
        "/domains/NOPE/extractions", json={"source_path": str(source_file)}, headers=auth_headers
    )
    _assert_envelope(resp, 400, "InvalidDomainError")


def test_review_bad_domain_maps_to_400_invalid_domain_error(client, auth_headers):
    resp = client.get("/domains/NOPE/proposals", headers=auth_headers)
    _assert_envelope(resp, 400, "InvalidDomainError")


def test_proposal_not_found_maps_to_404(client, auth_headers):
    resp = client.get("/domains/PERSONAL/proposals/prop-missing", headers=auth_headers)
    _assert_envelope(resp, 404, "ProposalNotFoundError")


def test_domain_mismatch_maps_to_400(client, auth_headers, make_proposal_file):
    # Filed on disk under PERSONAL (so read_proposal_file finds it via the
    # path domain), but its own frontmatter domain field says FICTION.
    proposal_id, _ = make_proposal_file(domain="PERSONAL", internal_domain="FICTION", status="PROPOSED")
    resp = client.get(f"/domains/PERSONAL/proposals/{proposal_id}", headers=auth_headers)
    _assert_envelope(resp, 400, "DomainMismatchError")


def test_invalid_proposal_status_maps_to_409(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(status="ACCEPTED")
    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "r1"},
        headers=auth_headers,
    )
    _assert_envelope(resp, 409, "InvalidProposalStatusError")


def test_unsupported_proposal_type_maps_to_422(client, auth_headers, make_proposal_file):
    proposal_id, _ = make_proposal_file(
        status="PROPOSED", proposed_item_type="entity", entity_type="person"
    )
    resp = client.post(
        f"/domains/PERSONAL/proposals/{proposal_id}/accept",
        json={"reviewer_id": "r1"},
        headers=auth_headers,
    )
    _assert_envelope(resp, 422, "UnsupportedProposalTypeError")


def test_unexpected_exception_maps_to_500(app, auth_headers):
    """Any exception type with no registered handler still yields the same
    JSON envelope, at 500."""

    @app.route("/_test/raise-unexpected")
    def _raise_unexpected():
        raise RuntimeError("something truly unexpected")

    client = app.test_client()
    _assert_envelope(client.get("/_test/raise-unexpected", headers=auth_headers), 500, "RuntimeError")


def test_swallowed_rows_are_wired_through_the_error_handler(app, auth_headers):
    """ExtractionValidationError/ReviewValidationError/ConfigError never propagate
    synchronously out of any current route (ingest_source/extract_source swallow
    them into a failed TaskState instead) - directly exercise the errorhandler
    wiring registered in create_app() for these rows."""

    @app.route("/_test/raise/<name>")
    def _raise(name):
        {
            "extraction_validation": lambda: (_ for _ in ()).throw(ExtractionValidationError("bad frontmatter")),
            "review_validation": lambda: (_ for _ in ()).throw(ReviewValidationError("bad frontmatter")),
            "config_error": lambda: (_ for _ in ()).throw(ConfigError("bad config")),
        }[name]()

    client = app.test_client()
    _assert_envelope(client.get("/_test/raise/extraction_validation", headers=auth_headers), 400, "ValidationError")
    _assert_envelope(client.get("/_test/raise/review_validation", headers=auth_headers), 400, "ValidationError")
    _assert_envelope(client.get("/_test/raise/config_error", headers=auth_headers), 500, "ConfigError")
