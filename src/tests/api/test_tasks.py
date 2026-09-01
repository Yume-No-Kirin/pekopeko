"""
load_task_state_resilient: TaskState.save() (ingestion/extraction
task_state.py) is not an atomic write, so a GET can transiently race the
background job's own next status-update write and see a truncated file -
load_task_state swallows that into None, indistinguishable from a
genuinely missing task, which would violate AC1 ("an immediate GET on
that task_id never returns 404"). These are deterministic, not
timing-dependent - the corrupt/missing file states are set up directly.
"""
from src.app.api.tasks import load_task_state_resilient


class _CountingLoader:
    """Simulates load_task_state: returns None a fixed number of times
    (as if racing a concurrent write), then a real TaskState."""

    def __init__(self, none_count, result):
        self.none_count = none_count
        self.result = result
        self.calls = 0

    def __call__(self, state_dir, task_id):
        self.calls += 1
        if self.calls <= self.none_count:
            return None
        return self.result


def test_retries_while_file_exists_until_it_parses(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    file_path = state_dir / "ingest-x.json"
    file_path.write_text("", encoding="utf-8")  # exists, but "unparseable" per the fake loader

    loader = _CountingLoader(none_count=3, result="a-task-state")

    result = load_task_state_resilient(loader, state_dir, "ingest-x", attempts=10, delay=0)

    assert result == "a-task-state"
    assert loader.calls == 4


def test_returns_none_immediately_when_file_never_existed(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    loader = _CountingLoader(none_count=100, result="a-task-state")

    result = load_task_state_resilient(loader, state_dir, "ingest-does-not-exist", attempts=10, delay=0)

    assert result is None
    assert loader.calls == 1  # no wasted retries for a genuinely missing task


def test_gives_up_after_max_attempts_if_still_unparseable(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "ingest-x.json").write_text("", encoding="utf-8")
    loader = _CountingLoader(none_count=100, result="a-task-state")

    result = load_task_state_resilient(loader, state_dir, "ingest-x", attempts=5, delay=0)

    assert result is None
