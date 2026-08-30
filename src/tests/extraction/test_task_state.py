"""
Task state record shape and status transitions.
"""
from unittest.mock import Mock

from _helpers import REPO_ROOT  # noqa: F401 (ensures repo root sys.path insertion runs first)

from src.app.extraction.task_state import (
    TaskState,
    create_task_state,
    update_task_state,
    load_task_state,
)
from src.app.extraction import extract_source, ExtractionResult


def test_create_task_state_defaults(tmp_path):
    state_dir = tmp_path / "state"
    task_state = create_task_state("some/source.md", "PERSONAL", state_dir)

    assert task_state.task_id.startswith("extract-")
    assert task_state.status == "pending"
    assert task_state.source_id is None
    assert task_state.proposal_ids == []
    assert task_state.error is None


def test_save_and_load_roundtrip(tmp_path):
    state_dir = tmp_path / "state"
    task_state = create_task_state("some/source.md", "PERSONAL", state_dir)
    task_state.status = "running"
    update_task_state(task_state, state_dir)

    loaded = load_task_state(state_dir, task_state.task_id)
    assert loaded is not None
    assert loaded.task_id == task_state.task_id
    assert loaded.status == "running"
    assert loaded.domain == "PERSONAL"


def test_load_missing_task_state_returns_none(tmp_path):
    state_dir = tmp_path / "state"
    assert load_task_state(state_dir, "extract-does-not-exist") is None


def test_pipeline_records_completed_status(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("content", encoding="utf-8")
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"

    provider = Mock()
    provider.extract.return_value = ExtractionResult()

    extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    state_files = list(state_dir.glob("extract-*.json"))
    assert len(state_files) == 1
    loaded = load_task_state(state_dir, state_files[0].stem)
    assert loaded.status == "completed"
    assert loaded.completed_at is not None


def test_pipeline_records_failed_status_with_error(tmp_path):
    source_file = tmp_path / "test.md"
    source_file.write_text("content", encoding="utf-8")
    vault_root = tmp_path / "vault"
    state_dir = tmp_path / "state"

    provider = Mock()
    provider.extract.side_effect = Exception("boom")

    extract_source(vault_root, "PERSONAL", source_file, provider, state_dir=state_dir)

    state_files = list(state_dir.glob("extract-*.json"))
    assert len(state_files) == 1
    loaded = load_task_state(state_dir, state_files[0].stem)
    assert loaded.status == "failed"
    assert "boom" in loaded.error
