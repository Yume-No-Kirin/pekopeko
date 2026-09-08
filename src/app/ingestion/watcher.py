"""
Background folder-watch ingestion trigger (ADI-013, TASK-001f/TASK-014b).

A daemon thread polls each domain's <vault_root>/<domain>/<inbox_dirname>/
tree for new, stable files and dispatches ingest_source automatically - no
manual API call or button press required. Recursive from the start (unlike
TASK-001f's original flat-only design): a file nested under a subfolder
(e.g. _inbox/sport/note.md) is discovered too, and that subfolder name is
the signal TASK-014b's OllamaProvider._derive_source_context reads back out
of the post-move source_path.

Independent of api/: run_in_background and the domain set are duplicated
here rather than imported, matching this codebase's "no module imports
another module's internals for shared constants" convention (already used
for VALID_DOMAINS across ingestion/pipeline.py, extraction/storage.py, and
api/domains.py) - importing from api/ would also invert the established
dependency direction (api/ depends on ingestion/, never the reverse).
"""
import logging
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Iterable, List

from .pipeline import ingest_source
from .task_state import create_task_state, update_task_state
from ..config.schema import FolderWatchConfig, PekopekoConfig

logger = logging.getLogger(__name__)

# Same fixed domain set as api/domains.py::VALID_DOMAINS - duplicated per this
# module's own independence convention (see module docstring), not imported.
_VALID_DOMAINS = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}


def _run_in_background(fn, *args, **kwargs) -> None:
    """Duplicate of api/tasks.py::run_in_background - see module docstring."""
    def _run():
        try:
            fn(*args, **kwargs)
        except Exception:
            logger.exception("Background task %s raised unexpectedly", getattr(fn, "__name__", fn))

    threading.Thread(target=_run, daemon=True).start()


def scan_once(
    vault_root: Path,
    domains: Iterable[str],
    config: FolderWatchConfig,
    provider,
    state_dir: Path,
) -> List[str]:
    """One poll tick, no sleep inside it - callable directly, deterministically,
    any number of times from a test. Returns the task_ids dispatched this tick.

    For each domain: resolves <vault_root>/<domain>/<inbox_dirname>/, creates
    it (and its <processed_dirname>/ subfolder) if missing, walks it
    recursively skipping dotfiles/dot-directories and the entire
    <processed_dirname>/ subtree at any depth, keeps only files whose mtime is
    older than poll_interval_seconds, and for each: first moves the file into
    <inbox_dirname>/<processed_dirname>/ (mirroring its relative subfolder
    path, not flattening it - suffixing on a name collision), then dispatches
    ingest_source with the post-move path. If the move itself fails, the file
    is skipped for this tick with a logged warning and no task is created.
    """
    dispatched: List[str] = []

    for domain in domains:
        inbox_dir = vault_root / domain / config.inbox_dirname
        processed_root = inbox_dir / config.processed_dirname
        inbox_dir.mkdir(parents=True, exist_ok=True)
        processed_root.mkdir(parents=True, exist_ok=True)

        # Materialized before any move happens: avoids iterator invalidation
        # from moving files into a subtree still being walked, and a
        # subfolder that disappears mid-scan must not raise (INV-019) - a
        # domain whose enumeration itself fails is skipped for this tick
        # rather than aborting the whole sweep across other domains.
        try:
            entries = list(inbox_dir.rglob("*"))
        except OSError:
            logger.warning("Failed to enumerate %s, skipping this tick", inbox_dir)
            continue

        for entry in entries:
            if not entry.is_file():
                continue
            try:
                rel = entry.relative_to(inbox_dir)
            except ValueError:
                continue
            if rel.parts[0] == config.processed_dirname:
                continue  # entire processed/ subtree, any depth
            if any(part.startswith(".") for part in rel.parts):
                continue  # dotfile/dot-directory anywhere in the relative path

            try:
                age_seconds = time.time() - entry.stat().st_mtime
            except OSError:
                continue
            if age_seconds < config.poll_interval_seconds:
                continue  # not yet stable - a later tick picks it up

            dest = processed_root / rel
            if dest.exists():
                dest = dest.with_name(f"{dest.stem}-{uuid.uuid4().hex[:8]}{dest.suffix}")
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(entry), str(dest))
            except OSError:
                logger.warning("Failed to move %s to %s, skipping this tick", entry, dest)
                continue

            task_id = f"ingest-{uuid.uuid4()}"
            task_state = create_task_state(str(dest), domain, state_dir, task_id=task_id)
            update_task_state(task_state, state_dir)
            _run_in_background(ingest_source, vault_root, domain, dest, provider, state_dir, task_id)
            dispatched.append(task_id)

    return dispatched


def start_folder_watcher(
    app_config: PekopekoConfig,
    vault_root: Path,
    provider,
    state_dir: Path,
) -> None:
    """No-ops immediately if folder_watch.enabled is False. Otherwise starts
    one daemon thread that calls scan_once(...) then sleeps
    poll_interval_seconds, forever, catching and logging any exception per
    iteration so the loop never dies silently."""
    if not app_config.folder_watch.enabled:
        return

    def _loop():
        while True:
            try:
                scan_once(vault_root, _VALID_DOMAINS, app_config.folder_watch, provider, state_dir)
            except Exception:
                logger.exception("Folder watcher tick failed")
            time.sleep(app_config.folder_watch.poll_interval_seconds)

    threading.Thread(target=_loop, daemon=True).start()
