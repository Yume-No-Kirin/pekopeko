"""
Background-thread helper for the async ingestion/extraction job contract
(ADI-010 SS2): a POST starts the existing blocking ingest_source/
extract_source call on a daemon thread, never blocking the HTTP response.
"""
import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def run_in_background(fn, *args, **kwargs) -> None:
    def _run():
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception("Background task %s raised unexpectedly", getattr(fn, "__name__", fn))

    threading.Thread(target=_run, daemon=True).start()


def load_task_state_resilient(load_task_state_fn, state_dir: Path, task_id: str,
                               attempts: int = 25, delay: float = 0.01):
    """
    TaskState.save() (ingestion/extraction task_state.py) is not an atomic
    write - a GET can race the background job's own very next status-update
    write and see a transiently truncated file, which load_task_state
    swallows into None indistinguishably from a genuinely missing task
    (AC1: "an immediate GET on that task_id never returns 404"). Retries
    briefly only while the file exists on disk but hasn't parsed yet -
    a task_id with no file at all (AC2/AC4) still returns None immediately.
    """
    file_path = state_dir / f"{task_id}.json"
    for _ in range(attempts):
        state = load_task_state_fn(state_dir, task_id)
        if state is not None:
            return state
        if not file_path.exists():
            return None
        time.sleep(delay)
    return load_task_state_fn(state_dir, task_id)
