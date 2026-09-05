# TASK-001f: Automatic Folder-Watch Ingestion Trigger

- **Status**: backlog

## Objective

Implement ADI-013: a background thread, started with the Flask app, that polls
`<vault_root>/<domain>/_inbox/` for each domain and dispatches `ingest_source` automatically on
any new, stable file found there — no manual API call or button press required. Extends TASK-001
(`completed`) additively — same posture already used by TASK-001a/b/c/d/e: no change to
`ingest_source`'s public signature, this ticket adds a new *caller* of the existing pipeline, not
a new code path inside it.

**Deliberate deviation from the TASK-001a/b/c/d pattern**: those satellites touched
`ingestion/`/`extraction/` internals (new fields, new events, failure/dedup logic) because the
gaps they closed were about what an extraction call *produces*. This ticket never touches what
`ingest_source` produces — it only decides *when* `ingest_source` gets called, by reusing the
exact same dispatch shape `src/app/api/routes_ingestion.py` already uses for the manual HTTP
trigger.

## Binding context (references, not duplicated here)

- **ADI-013** (`specs/decisions/ADI-013-automatic-folder-ingestion.md`, Accepted): the decision
  this ticket implements in full — polling mechanism, per-domain `_inbox/` location,
  move-to-`processed/` on dispatch, in-process daemon thread, settle rule, config shape, failure
  posture. Read it in full before implementing anything here.
- **TASK-001** (`specs/tasks/completed/TASK-001-data-ingestion.md`, `completed`): the pipeline
  this ticket triggers automatically. `ingest_source`'s signature is not changed.
- `src/app/api/routes_ingestion.py:30-52` (`start_ingestion`) — the exact dispatch shape to
  reuse: mint a `task_id`, `create_task_state(...)`, `update_task_state(...)`, then
  `run_in_background(ingest_source, vault_root, domain, Path(source_path), provider, state_dir,
  task_id)`. This ticket's watcher calls the same four functions per detected file instead of a
  single one per HTTP request.
- `src/app/api/tasks.py:14-21` (`run_in_background`) — the daemon-thread pattern already used for
  one-shot ingestion jobs; this ticket's `start_folder_watcher` extends the same posture to a
  long-running poll loop rather than a one-shot call.
- `src/app/config/loader.py` (`_build_config`, `_apply_env_overrides`) and
  `src/app/config/schema.py` (`TaskStateConfig`/`RetrievalConfig` as the closest precedent) —
  where the new `folder_watch` config section is added, following the exact same
  defaults-then-file-then-env resolution order already established there.
- `src/app/api/domains.py` (`VALID_DOMAINS`) — the fixed set of domains the watcher scans; no new
  domain-discovery logic.
- `src/app/api/app.py` (`create_app`) — where `start_folder_watcher` is invoked once, after the
  app and its config are fully constructed.

## Scope

1. `src/app/config/schema.py` gains `FolderWatchConfig`: `enabled: bool = False`,
   `poll_interval_seconds: int = 30`, `inbox_dirname: str = "_inbox"`,
   `processed_dirname: str = "processed"`. `PekopekoConfig` gains a `folder_watch:
   FolderWatchConfig` field, defaulting to `FolderWatchConfig()` when the section is absent from
   `config.yaml` — same absent-is-default posture as every other config section.
2. `src/app/config/loader.py`: `_build_config` reads an optional `folder_watch` mapping the same
   way `_require_mapping` already handles `task_state`/`retrieval`, with validation mirroring
   `_validate_timeout` (positive-integer check on `poll_interval_seconds`, non-empty-string checks
   on `inbox_dirname`/`processed_dirname`). No new `PEKOPEKO_*` environment variable — this section
   is file-only, matching ADI-010's accepted asymmetry for options that don't need process-level
   override.
3. New module `src/app/ingestion/watcher.py`:
   - `scan_once(vault_root: Path, domains: Iterable[str], config: FolderWatchConfig, provider,
     state_dir: Path) -> list[str]` — one poll tick, no sleep inside it (so tests call it
     directly, deterministically, any number of times). For each domain: resolves
     `<vault_root>/<domain>/<inbox_dirname>/`, creates it (and its `<processed_dirname>/`
     subfolder) if missing, lists direct children skipping dotfiles and the `processed_dirname`
     subfolder itself, keeps only files whose mtime is older than `poll_interval_seconds`, and for
     each: mints `task_id = f"ingest-{uuid.uuid4()}"`, calls `create_task_state`/
     `update_task_state`, dispatches `ingest_source` via `run_in_background`, then moves the file
     into `<inbox_dirname>/<processed_dirname>/` (on a name collision, append a short uuid suffix
     before the extension). Returns the list of dispatched `task_id`s for test assertions.
   - `start_folder_watcher(app_config: PekopekoConfig, vault_root: Path, provider, state_dir:
     Path) -> None` — no-ops immediately if `app_config.folder_watch.enabled` is `False`;
     otherwise starts one daemon thread that calls `scan_once(...)` then sleeps
     `poll_interval_seconds`, forever, catching and logging any exception per iteration (same
     "never let a background loop die silently" posture `run_in_background` already applies to
     one-shot jobs).
4. `src/app/api/app.py` (`create_app`): after building the app and loading config, calls
   `start_folder_watcher(config, vault_root, build_configured_provider(config), state_dir)` once,
   before returning the app.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No automatic retry on ingestion failure. The source file is already in `processed/` once
  dispatch happens (not once ingestion succeeds) — recovering from a failed ingestion is a manual
  action (move the file back into `_inbox/`), consistent with ADI-005's stated fallback that lost/
  failed task state means the task "must be resubmitted", never silently redone.
- No distinction in the Ingestion Logs screen (TASK-009) between a manually-triggered and a
  watcher-triggered task — both use the identical `ingest-<uuid>` task-id shape and flow through
  identical task-state records. Surfacing the origin is not this ticket's scope.
- No OS-level filesystem watcher — polling only, per ADI-013.
- No Settings-screen UI to toggle `folder_watch.enabled` — a `config.yaml` setting in V1, same as
  every other config value this app already has no dedicated write-UI for.
- No new source-format support — the watcher hands the same file paths to the same
  `ingest_source`/provider pipeline TASK-001/003 already parse; whatever formats they already
  accept are all this ticket accepts.

## Requirements

Python only, no new dependency (`watchdog` explicitly rejected by ADI-013). Same testing
discipline as TASK-001a-e: `pytest`, `tmp_path` standing in for `vault_root`, a mocked/fake
provider (no real Ollama call in the default test suite), no real `time.sleep` in tests — `scan_once`
must be callable and assertable without going through `start_folder_watcher`'s loop at all.

## Constraints

- No change to `ingest_source`'s public signature or to `create_task_state`/`update_task_state`.
- `folder_watch.enabled` defaults to `False` — installing this ticket must not change the
  observable behavior of any existing deployment that doesn't opt in via `config.yaml`.
- The watcher never blocks on an ingestion's completion — `scan_once` dispatches via
  `run_in_background` and returns; a slow or hung extraction must not delay detection of other
  files or other domains.
- A domain with no `_inbox/` folder yet must not raise — the folder is created on first tick, not
  required to pre-exist.

## Files/modules concerned

- `src/app/config/schema.py` (`FolderWatchConfig`, `PekopekoConfig`)
- `src/app/config/loader.py` (`_build_config`)
- New: `src/app/ingestion/watcher.py` (`scan_once`, `start_folder_watcher`)
- `src/app/api/app.py` (`create_app`)
- New/updated tests in `src/tests/ingestion/` and `src/tests/config/` mirroring the existing
  structure: config defaults/overrides for `folder_watch`; `scan_once` behavior for a stable file,
  an unstable (too-recent) file, a domain with no `_inbox/` yet, a dotfile, an already-`processed/`
  file, and a name collision in `processed/`.

## Dependencies

TASK-001 (`completed`) and ADI-013 (Accepted). Independent of TASK-005/TASK-012/TASK-001e/
TASK-014 — this ticket is a new trigger path, not a change to review, extraction, or folder-path
organization logic.

## Acceptance criteria

1. `FolderWatchConfig` loads with defaults (`enabled=False`, `poll_interval_seconds=30`,
   `inbox_dirname="_inbox"`, `processed_dirname="processed"`) when the `folder_watch` section is
   absent from `config.yaml`.
2. An explicit `folder_watch` section in `config.yaml` overrides any subset of the four fields;
   omitted fields keep their default.
3. An invalid `poll_interval_seconds` (non-positive, non-integer) raises `ConfigError`, same
   pattern as `_validate_timeout`.
4. With `enabled=False`, `start_folder_watcher` starts no thread and calling it has no observable
   side effect.
5. `scan_once` dispatches `ingest_source` (verified via a fake `run_in_background`/provider) for a
   file in `<vault_root>/<domain>/_inbox/` whose mtime is older than `poll_interval_seconds`.
6. `scan_once` does not dispatch a file whose mtime is more recent than `poll_interval_seconds` —
   it remains in `_inbox/` for a later tick to pick up.
7. After a successful dispatch, the source file is present in
   `_inbox/<processed_dirname>/` and absent from `_inbox/`.
8. A name collision in `processed/` is resolved by suffixing, never by overwriting an existing
   processed file.
9. Dotfiles and the `processed_dirname` subfolder itself are never dispatched.
10. A domain whose `_inbox/` folder doesn't exist yet does not raise; the folder (and its
    `processed/` subfolder) is created and the domain contributes no dispatches that tick.
11. `scan_once` returns the `task_id`s it dispatched, enabling direct test assertions without
    inspecting task-state files.
12. `ingest_source`'s public signature is unchanged (regression check by direct comparison).

## Testing requirements

`pytest`, `tmp_path`, a fake/mocked provider and a stubbed `run_in_background` (capturing calls
instead of spawning real threads) — no real Ollama call, no real `time.sleep`, covering AC1-12.
Project-wide bar: at least 80% coverage on every file touched.

## Out of scope

- Any OS-level filesystem watcher (`watchdog` or similar).
- Automatic retry of a failed watcher-dispatched ingestion.
- Any UI (Settings screen or otherwise) to toggle or configure `folder_watch` — `config.yaml`
  only in V1.
- Distinguishing watcher-triggered from manually-triggered tasks in the Ingestion Logs screen
  (TASK-009) or anywhere else in the API/frontend.
- New source-file-format support beyond what `ingest_source`/its providers already accept.
