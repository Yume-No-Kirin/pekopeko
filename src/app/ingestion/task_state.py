"""
Task state management for ingestion pipeline.
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid


@dataclass
class TaskEvent:
    """A single timestamped step recorded during an ingestion task attempt."""
    timestamp: str  # ISO 8601
    level: str  # "info" | "success" | "warning"
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'level': self.level,
            'message': self.message,
            'details': self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskEvent':
        return cls(**data)


class TaskState:
    """Represents the state of an ingestion task."""

    def __init__(
        self,
        task_id: str,
        source_path: str,
        domain: str,
        status: str = "pending",
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        error: Optional[str] = None,
        source_id: Optional[str] = None,
        proposal_ids: Optional[list[str]] = None,
        events: Optional[List[TaskEvent]] = None
    ):
        self.task_id = task_id
        self.source_path = source_path
        self.domain = domain
        self.status = status  # pending, running, completed, failed, skipped_duplicate
        self.started_at = started_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.error = error
        self.source_id = source_id
        self.proposal_ids = proposal_ids or []
        self.events = events or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert task state to dictionary."""
        return {
            'task_id': self.task_id,
            'source_path': self.source_path,
            'domain': self.domain,
            'status': self.status,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'source_id': self.source_id,
            'proposal_ids': self.proposal_ids,
            'events': [event.to_dict() for event in self.events]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskState':
        """Create task state from dictionary. Tolerates a missing 'events' key
        (TaskState files persisted before this field existed)."""
        data = dict(data)
        events_data = data.pop('events', [])
        events = [TaskEvent.from_dict(event) for event in events_data]
        return cls(events=events, **data)

    def save(self, state_dir: Path):
        """
        Save task state to disk.

        Args:
            state_dir: Directory where task state should be saved
        """
        # Create directory if it doesn't exist
        state_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename from task_id
        filename = f"{self.task_id}.json"
        file_path = state_dir / filename

        # Write to file atomically using JSON
        data = self.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def load_task_state(state_dir: Path, task_id: str) -> Optional[TaskState]:
    """
    Load task state from disk.

    Args:
        state_dir: Directory where task state is saved
        task_id: ID of the task to load

    Returns:
        TaskState object or None if not found
    """
    filename = f"{task_id}.json"
    file_path = state_dir / filename

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return TaskState.from_dict(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def create_task_state(
    source_path: str,
    domain: str,
    state_dir: Path,
    task_id: Optional[str] = None
) -> TaskState:
    """
    Create a new task state.

    Args:
        source_path: Path to the source file
        domain: Domain name
        state_dir: Directory for task state storage
        task_id: Pre-minted task id to use verbatim (optional). If not given,
            a new id is minted as before.

    Returns:
        New TaskState object
    """
    if task_id is None:
        task_id = f"ingest-{uuid.uuid4()}"
    return TaskState(
        task_id=task_id,
        source_path=source_path,
        domain=domain,
        status="pending"
    )


def list_task_states(state_dir: Path) -> List[TaskState]:
    """
    List all task states persisted under state_dir.

    Args:
        state_dir: Directory for task state storage

    Returns:
        TaskState objects for every parseable *.json file in state_dir.
        Files that fail to parse are skipped, same swallow behavior as
        load_task_state.
    """
    if not state_dir.exists():
        return []

    states = []
    for file_path in sorted(state_dir.glob("*.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            states.append(TaskState.from_dict(data))
        except (json.JSONDecodeError, OSError, TypeError, KeyError):
            continue
    return states


def update_task_state(task_state: TaskState, state_dir: Path):
    """
    Update task state on disk.

    Args:
        task_state: TaskState object to save
        state_dir: Directory for task state storage
    """
    task_state.save(state_dir)


def append_task_event(
    task_state: TaskState,
    state_dir: Path,
    level: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Append one TaskEvent to task_state.events and persist the updated
    TaskState via the existing save/update_task_state write path.

    Args:
        task_state: TaskState object to append the event to
        state_dir: Directory for task state storage
        level: One of "info", "success", "warning"
        message: Human-readable description of the step
        details: Optional free-form JSON-serializable context
    """
    task_state.events.append(TaskEvent(
        timestamp=datetime.now().isoformat(),
        level=level,
        message=message,
        details=details
    ))
    update_task_state(task_state, state_dir)