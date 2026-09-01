"""
Shared test-only helpers for api/ tests.

Kept out of conftest.py so test modules can import them directly (fixtures
alone can't be imported by name) without a bare `from conftest import ...`,
which resolves ambiguously across test directories that each have their own
conftest.py of the same module name.
"""
import json
import time
from pathlib import Path

from src.app.extraction.providers.base import ExtractionResult as ExtractionProviderResult
from src.app.ingestion.providers.base import ExtractionResult as IngestionProviderResult


class FakeIngestionProvider:
    def __init__(self, result=None, exc=None):
        self.result = result if result is not None else IngestionProviderResult(assertions=[])
        self.exc = exc
        self.calls = 0

    def extract(self, text, context):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.result


class FakeExtractionProvider:
    def __init__(self, result=None, exc=None):
        self.result = result if result is not None else ExtractionProviderResult()
        self.exc = exc
        self.calls = 0

    def extract(self, text, context):
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return self.result


def wait_for_terminal_status(state_dir: Path, task_id: str, subdir: str, timeout: float = 5.0):
    """Poll the on-disk TaskState until it leaves pending/running, or timeout.

    The background writer thread is not using an atomic rename for this file
    (unlike review/storage.py), so a read can race an in-progress write and
    see empty/partial content - treated as "not yet ready" and retried,
    rather than a test failure.
    """
    deadline = time.monotonic() + timeout
    task_dir = state_dir / subdir
    while time.monotonic() < deadline:
        file_path = task_dir / f"{task_id}.json"
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = None
            if data is not None and data["status"] not in ("pending", "running"):
                return data
        time.sleep(0.02)
    raise TimeoutError(f"Task {task_id} did not reach a terminal status within {timeout}s")
