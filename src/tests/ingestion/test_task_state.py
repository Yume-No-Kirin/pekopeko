"""
Task event log: TaskEvent/append_task_event, from_dict backward compatibility,
save/load round-trip (TASK-001b).
"""
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.ingestion.task_state import (
    TaskState,
    TaskEvent,
    create_task_state,
    update_task_state,
    load_task_state,
    append_task_event,
)


def test_create_task_state_has_empty_events_by_default(tmp_path):
    state_dir = tmp_path / "state"
    task_state = create_task_state("some/source.md", "PERSONAL", state_dir)

    assert task_state.events == []


def test_append_task_event_appends_and_persists(tmp_path):
    state_dir = tmp_path / "state"
    task_state = create_task_state("some/source.md", "PERSONAL", state_dir)
    update_task_state(task_state, state_dir)

    append_task_event(task_state, state_dir, "info", "Step one", {"key": "value"})
    append_task_event(task_state, state_dir, "success", "Step two")

    assert len(task_state.events) == 2
    assert task_state.events[0].level == "info"
    assert task_state.events[0].message == "Step one"
    assert task_state.events[0].details == {"key": "value"}
    assert task_state.events[1].level == "success"
    assert task_state.events[1].details is None

    loaded = load_task_state(state_dir, task_state.task_id)
    assert len(loaded.events) == 2
    assert loaded.events[0].message == "Step one"


def test_from_dict_tolerates_missing_events_key(tmp_path):
    """AC5: a TaskState dict persisted before this ticket (no 'events' key)
    loads without error and yields events == []."""
    legacy_data = {
        "task_id": "ingest-legacy",
        "source_path": "legacy.md",
        "domain": "PERSONAL",
        "status": "completed",
        "started_at": "2026-01-01T00:00:00",
        "completed_at": "2026-01-01T00:00:01",
        "error": None,
        "source_id": "src-legacy",
        "proposal_ids": ["prop-1"],
    }

    task_state = TaskState.from_dict(legacy_data)

    assert task_state.events == []
    assert task_state.task_id == "ingest-legacy"
    assert task_state.proposal_ids == ["prop-1"]


def test_events_round_trip_through_save_and_load(tmp_path):
    """AC6: events entries are JSON-serializable and round-trip correctly
    through save()/load_task_state() - timestamp, level, message, details
    all preserved."""
    state_dir = tmp_path / "state"
    task_state = create_task_state("some/source.md", "PERSONAL", state_dir)
    update_task_state(task_state, state_dir)

    append_task_event(
        task_state, state_dir, "warning", "Something happened",
        {"source_id": "src-abc", "count": 3}
    )

    loaded = load_task_state(state_dir, task_state.task_id)

    assert len(loaded.events) == 1
    loaded_event = loaded.events[0]
    original_event = task_state.events[0]
    assert isinstance(loaded_event, TaskEvent)
    assert loaded_event.timestamp == original_event.timestamp
    assert loaded_event.level == "warning"
    assert loaded_event.message == "Something happened"
    assert loaded_event.details == {"source_id": "src-abc", "count": 3}
