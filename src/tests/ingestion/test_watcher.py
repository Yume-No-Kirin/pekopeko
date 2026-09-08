"""
Unit tests for ingestion/watcher.py (ADI-013, TASK-001f/TASK-014b): scan_once's
recursive _inbox/ polling, move-before-dispatch ordering, and
start_folder_watcher's enable/no-op gating and background loop.

No real network calls, no real time.sleep - run_in_background is monkeypatched
to a synchronous capture instead of spawning a real thread, so scan_once's
dispatches are directly assertable.
"""
import os
import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.app.ingestion import watcher
from src.app.config.schema import FolderWatchConfig, PekopekoConfig


def _capture_dispatches(monkeypatch):
    """Replaces watcher._run_in_background with a synchronous capture,
    returning the list it appends (fn, args, kwargs) tuples to."""
    calls = []

    def fake_run_in_background(fn, *args, **kwargs):
        calls.append((fn, args, kwargs))

    monkeypatch.setattr(watcher, "_run_in_background", fake_run_in_background)
    return calls


def _age_file(path: Path, seconds_old: float) -> None:
    old_time = time.time() - seconds_old
    os.utime(path, (old_time, old_time))


def _make_config(**overrides) -> FolderWatchConfig:
    defaults = dict(enabled=True, poll_interval_seconds=30, inbox_dirname="_inbox", processed_dirname="processed")
    defaults.update(overrides)
    return FolderWatchConfig(**defaults)


# --- scan_once: discovery, staleness, dispatch ---

def test_scan_once_dispatches_stable_file_with_post_move_path(tmp_path, monkeypatch):
    """AC5: dispatches ingest_source for a file whose mtime is older than
    poll_interval_seconds, with the post-move path - which exists on disk at
    the moment of dispatch (move-before-dispatch ordering, AC7)."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    source_file = inbox / "note.md"
    source_file.write_text("content", encoding="utf-8")
    _age_file(source_file, 60)

    config = _make_config(poll_interval_seconds=30)
    provider = Mock()
    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], config, provider, tmp_path / "state")

    assert len(task_ids) == 1
    assert len(calls) == 1
    fn, args, kwargs = calls[0]
    assert fn is watcher.ingest_source
    dispatched_vault_root, dispatched_domain, dispatched_path, dispatched_provider, dispatched_state_dir, dispatched_task_id = args
    assert dispatched_vault_root == tmp_path
    assert dispatched_domain == "PERSONAL"
    assert dispatched_path == inbox / "processed" / "note.md"
    assert dispatched_path.exists()
    assert dispatched_provider is provider
    assert dispatched_task_id == task_ids[0]


def test_scan_once_does_not_dispatch_recent_file(tmp_path, monkeypatch):
    """AC6: a file whose mtime is more recent than poll_interval_seconds stays
    in _inbox/ for a later tick."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    source_file = inbox / "note.md"
    source_file.write_text("content", encoding="utf-8")
    _age_file(source_file, 1)

    config = _make_config(poll_interval_seconds=30)
    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], config, Mock(), tmp_path / "state")

    assert task_ids == []
    assert calls == []
    assert source_file.exists()


def test_scan_once_moves_source_present_absent_from_inbox_after_dispatch(tmp_path, monkeypatch):
    """AC7: after a successful dispatch, the source file is present in
    processed/ and absent from _inbox/."""
    _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    source_file = inbox / "note.md"
    source_file.write_text("content", encoding="utf-8")
    _age_file(source_file, 60)

    watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert not source_file.exists()
    assert (inbox / "processed" / "note.md").exists()


def test_scan_once_recursive_discovery_mirrors_subfolder_in_processed(tmp_path, monkeypatch):
    """AC11 (TASK-014b): a file nested one level under _inbox/ is discovered,
    moved to _inbox/processed/<subfolder>/file.md - mirrored, not flattened."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    (inbox / "sport").mkdir(parents=True)
    source_file = inbox / "sport" / "note.md"
    source_file.write_text("content", encoding="utf-8")
    _age_file(source_file, 60)

    watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    dest = inbox / "processed" / "sport" / "note.md"
    assert dest.exists()
    assert not source_file.exists()
    fn, args, kwargs = calls[0]
    assert args[2] == dest


def test_scan_once_skips_processed_subtree_at_any_depth(tmp_path, monkeypatch):
    """AC9/AC12: the processed_dirname subfolder itself is never dispatched,
    including files nested deeper inside it."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    processed = inbox / "processed"
    (processed / "sport").mkdir(parents=True)
    already_processed = processed / "sport" / "old-note.md"
    already_processed.write_text("content", encoding="utf-8")
    _age_file(already_processed, 60)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert task_ids == []
    assert calls == []
    assert already_processed.exists()


def test_scan_once_skips_dotfiles_and_dot_directories(tmp_path, monkeypatch):
    """AC9."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    dotfile = inbox / ".DS_Store"
    dotfile.write_text("x", encoding="utf-8")
    _age_file(dotfile, 60)
    (inbox / ".hidden").mkdir()
    nested_in_dot_dir = inbox / ".hidden" / "note.md"
    nested_in_dot_dir.write_text("x", encoding="utf-8")
    _age_file(nested_in_dot_dir, 60)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert task_ids == []
    assert calls == []


def test_scan_once_missing_inbox_creates_it_and_dispatches_nothing(tmp_path, monkeypatch):
    """AC10: a domain whose _inbox/ doesn't exist yet does not raise; the
    folder (and its processed/ subfolder) is created, no dispatches that tick."""
    calls = _capture_dispatches(monkeypatch)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert task_ids == []
    assert calls == []
    assert (tmp_path / "PERSONAL" / "_inbox").exists()
    assert (tmp_path / "PERSONAL" / "_inbox" / "processed").exists()


def test_scan_once_name_collision_in_processed_resolved_by_suffixing(tmp_path, monkeypatch):
    """AC8: a name collision in processed/ is resolved by suffixing, never by
    overwriting an existing processed file."""
    _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    processed = inbox / "processed"
    processed.mkdir(parents=True)
    existing = processed / "note.md"
    existing.write_text("existing content", encoding="utf-8")

    new_file = inbox / "note.md"
    new_file.write_text("new content", encoding="utf-8")
    _age_file(new_file, 60)

    watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert existing.read_text(encoding="utf-8") == "existing content"
    processed_files = sorted(p.name for p in processed.iterdir())
    assert len(processed_files) == 2
    new_name = [n for n in processed_files if n != "note.md"][0]
    assert (processed / new_name).read_text(encoding="utf-8") == "new content"


def test_scan_once_returns_dispatched_task_ids(tmp_path, monkeypatch):
    """AC11 (TASK-001f numbering)."""
    _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    for name in ("a.md", "b.md"):
        f = inbox / name
        f.write_text("content", encoding="utf-8")
        _age_file(f, 60)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert len(task_ids) == 2
    assert all(tid.startswith("ingest-") for tid in task_ids)


def test_scan_once_failing_move_dispatches_nothing_but_other_files_still_processed(tmp_path, monkeypatch):
    """AC13: if the move raises, no task state is created and no dispatch
    happens for that file; the tick completes and other files in the same
    _inbox/ are still processed."""
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    bad_file = inbox / "bad.md"
    bad_file.write_text("content", encoding="utf-8")
    _age_file(bad_file, 60)
    good_file = inbox / "good.md"
    good_file.write_text("content", encoding="utf-8")
    _age_file(good_file, 60)

    real_move = watcher.shutil.move

    def flaky_move(src, dst):
        if "bad" in str(src):
            raise OSError("simulated move failure")
        return real_move(src, dst)

    monkeypatch.setattr(watcher.shutil, "move", flaky_move)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert len(task_ids) == 1
    assert len(calls) == 1
    assert bad_file.exists()  # never moved
    assert not (inbox / "processed" / "bad.md").exists()
    assert (inbox / "processed" / "good.md").exists()


def test_scan_once_missing_subfolder_mid_scan_does_not_raise_other_domains_still_processed(tmp_path, monkeypatch):
    """Constraint: a subfolder that disappears mid-scan must not raise, and
    must not prevent other domains' ticks in the same call."""
    _capture_dispatches(monkeypatch)
    personal_inbox = tmp_path / "PERSONAL" / "_inbox"
    personal_inbox.mkdir(parents=True)
    fiction_inbox = tmp_path / "FICTION" / "_inbox"
    fiction_inbox.mkdir(parents=True)
    good_file = fiction_inbox / "note.md"
    good_file.write_text("content", encoding="utf-8")
    _age_file(good_file, 60)

    real_rglob = Path.rglob

    def flaky_rglob(self, pattern):
        if self == personal_inbox:
            raise OSError("simulated enumeration failure")
        return real_rglob(self, pattern)

    monkeypatch.setattr(Path, "rglob", flaky_rglob)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL", "FICTION"], _make_config(), Mock(), tmp_path / "state")

    assert len(task_ids) == 1


# --- _run_in_background: real (non-monkeypatched) dispatch ---

def test_run_in_background_invokes_fn_on_a_daemon_thread():
    done = threading.Event()
    captured_args = []

    def fn(a, b):
        captured_args.append((a, b))
        done.set()

    watcher._run_in_background(fn, 1, 2)

    assert done.wait(timeout=5)
    assert captured_args == [(1, 2)]


def test_run_in_background_logs_and_swallows_exception():
    done = threading.Event()

    def failing_fn():
        done.set()
        raise RuntimeError("boom")

    # Must not raise out of the calling thread - the exception is caught and
    # logged inside the background thread.
    watcher._run_in_background(failing_fn)

    assert done.wait(timeout=5)


# --- scan_once: mtime-stat race (file vanishes between listing and stat) ---

def test_scan_once_file_vanishing_before_stat_is_skipped_not_raised(tmp_path, monkeypatch):
    calls = _capture_dispatches(monkeypatch)
    inbox = tmp_path / "PERSONAL" / "_inbox"
    inbox.mkdir(parents=True)
    vanishing_file = inbox / "vanishing.md"
    vanishing_file.write_text("content", encoding="utf-8")
    _age_file(vanishing_file, 60)

    real_stat = Path.stat
    call_count = {"n": 0}

    def flaky_stat(self, *args, **kwargs):
        # is_file() also calls .stat() internally - let its own call through,
        # and only fail the later, explicit mtime-check call.
        if self.name == "vanishing.md":
            call_count["n"] += 1
            if call_count["n"] > 1:
                raise OSError("simulated: file vanished before stat")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", flaky_stat)

    task_ids = watcher.scan_once(tmp_path, ["PERSONAL"], _make_config(), Mock(), tmp_path / "state")

    assert task_ids == []
    assert calls == []


# --- start_folder_watcher: enable gating, loop wiring ---

def test_start_folder_watcher_noop_when_disabled(tmp_path, monkeypatch):
    """AC4."""
    thread_calls = []
    monkeypatch.setattr(watcher.threading, "Thread", lambda *a, **k: thread_calls.append((a, k)))

    config = PekopekoConfig(folder_watch=FolderWatchConfig(enabled=False))
    watcher.start_folder_watcher(config, tmp_path, Mock(), tmp_path / "state")

    assert thread_calls == []


def test_start_folder_watcher_enabled_starts_daemon_thread_calling_scan_once(tmp_path, monkeypatch):
    captured = {}

    class FakeThread:
        def __init__(self, target, daemon):
            captured["target"] = target
            captured["daemon"] = daemon

        def start(self):
            captured["started"] = True

    monkeypatch.setattr(watcher.threading, "Thread", FakeThread)

    scan_calls = []
    monkeypatch.setattr(watcher, "scan_once", lambda *a, **k: scan_calls.append(1))

    def fake_sleep(seconds):
        # Breaks the intentionally-infinite loop after one iteration, without
        # a real sleep - time.sleep sits outside scan_once's try/except, so
        # this exception propagates straight out of the loop function.
        raise RuntimeError("stop after one iteration")

    monkeypatch.setattr(watcher.time, "sleep", fake_sleep)

    config = PekopekoConfig(folder_watch=FolderWatchConfig(enabled=True, poll_interval_seconds=1))
    watcher.start_folder_watcher(config, tmp_path, Mock(), tmp_path / "state")

    assert captured["daemon"] is True
    assert captured["started"] is True

    with pytest.raises(RuntimeError, match="stop after one iteration"):
        captured["target"]()
    assert scan_calls == [1]


def test_start_folder_watcher_loop_swallows_scan_once_exception(tmp_path, monkeypatch):
    """Never let the background loop die silently - an exception during
    scan_once is caught and logged, the loop still reaches time.sleep."""
    captured = {}

    class FakeThread:
        def __init__(self, target, daemon):
            captured["target"] = target

        def start(self):
            pass

    monkeypatch.setattr(watcher.threading, "Thread", FakeThread)
    monkeypatch.setattr(watcher, "scan_once", Mock(side_effect=RuntimeError("boom")))

    def fake_sleep(seconds):
        raise RuntimeError("reached sleep")

    monkeypatch.setattr(watcher.time, "sleep", fake_sleep)

    config = PekopekoConfig(folder_watch=FolderWatchConfig(enabled=True, poll_interval_seconds=1))
    watcher.start_folder_watcher(config, tmp_path, Mock(), tmp_path / "state")

    with pytest.raises(RuntimeError, match="reached sleep"):
        captured["target"]()
