"""
Direct unit coverage for the JSON-dict helpers not currently exercised by any
route (ingestion_result_to_dict/extraction_result_to_dict serialize the
synchronous return value of ingest_source()/extract_source(), which the
async job endpoints don't put in an HTTP response body today - only the
polled TaskState is - but the ticket's Files/modules concerned section
still requires both helpers to exist).
"""
from src.app.extraction.pipeline import ExtractionPipelineResult
from src.app.ingestion.pipeline import IngestionResult

from src.app.api.serialization import batch_response, extraction_result_to_dict, ingestion_result_to_dict


def test_ingestion_result_to_dict():
    result = IngestionResult(
        source_id="src-1", proposal_ids=["prop-1", "prop-2"], status="completed",
        error=None, skipped_duplicate=False,
    )
    assert ingestion_result_to_dict(result) == {
        "source_id": "src-1",
        "proposal_ids": ["prop-1", "prop-2"],
        "status": "completed",
        "error": None,
        "skipped_duplicate": False,
    }


def test_extraction_result_to_dict():
    result = ExtractionPipelineResult(
        source_id="src-2", proposal_ids=["prop-3"], status="failed",
        error="boom", skipped_duplicate=False,
    )
    assert extraction_result_to_dict(result) == {
        "source_id": "src-2",
        "proposal_ids": ["prop-3"],
        "status": "failed",
        "error": "boom",
        "skipped_duplicate": False,
    }


def test_batch_response_counts_and_preserves_order():
    results = [
        {"proposal_id": "p1", "status": "accepted"},
        {"proposal_id": "p2", "status": "failed", "error": {"type": "ProposalNotFoundError", "message": "boom"}},
        {"proposal_id": "p3", "status": "accepted"},
    ]

    envelope = batch_response(results)

    assert envelope["results"] == results
    assert envelope["succeeded_count"] == 2
    assert envelope["failed_count"] == 1
