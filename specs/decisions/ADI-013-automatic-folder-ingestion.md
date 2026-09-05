# ADI-013: Automatic Folder-Watch Ingestion Trigger

- **ID**: ADI-013
- **Date**: 2026-09-04
- **Status**: Accepted (confirmed by Cleo on 2026-09-04)

## Context

Every ingestion trigger documented or implemented so far is manual/explicit. TASK-001
(`completed`) states plainly: *"No GUI or CLI required (a Python function entry point is
sufficient)"* — `ingest_source(vault_root, domain, source_path, provider, ...)` is called with a
caller-supplied `source_path`. The HTTP layer built on top (`POST /domains/<domain>/ingestions`,
`src/app/api/routes_ingestion.py`) requires `source_path` in the request body and raises if it is
missing; there is no endpoint that discovers a file on its own. TASK-009 (Ingestion Logs screen,
`completed`) even left the mockup's "+ Nouvelle ingestion" button unported, so the manual path
isn't fully wired up on the frontend either.

Nothing in this corpus ever asked the question this ADR answers: should dropping a file into a
watched folder be enough to start extraction, with no explicit API call or button press? A grep
across `BACKLOG-CLAUDE.md`/`BACKLOG-CLAUDE-V2.md` for watch/watcher/surveil/inbox returns nothing
— this is not a "stay manual" decision being revisited, it is a gap being closed for the first
time, the same way ADI-012 closed the open fork ADI-004 had deliberately left for the folder-path
builder.

## Decision

**A background thread inside the existing Flask process periodically polls a per-domain inbox
folder and dispatches ingestion automatically for any stable file it finds**, reusing
`ingest_source`/`create_task_state`/`build_configured_provider` exactly as
`routes_ingestion.py` already does — a watcher-triggered ingestion is indistinguishable from a
manually-triggered one anywhere downstream (task state, Ingestion Logs screen).

Four points, each confirmed explicitly by Cleo:

1. **Mechanism: periodic polling, not an OS-level filesystem watcher.** No new dependency (e.g.
   `watchdog`), no cross-platform event-API divergence to handle (Windows/macOS/Linux, network
   drives). A short delay between drop and detection is acceptable for a personal
   knowledge-ingestion tool — consistent with AGENTS.md's Simplicity First.
2. **Location: one inbox per domain**, `<vault_root>/<domain>/_inbox/`. Consistent with Domain
   Isolation (AP-005), already treated as load-bearing by ADI-004 and reaffirmed by ADI-012's own
   `<domain>`-prefix reasoning — the domain is known unambiguously the moment a file is detected,
   with no separate selection step.
3. **Post-processing: the source file is moved to `<vault_root>/<domain>/_inbox/processed/`**
   once ingestion has been *dispatched* (not necessarily finished) for it. This removes the file
   from the watched set immediately, so a later poll tick can never re-detect it — no dependency
   on TASK-001d's duplicate-detection to prevent a double ingestion from repeated polling.
4. **Lifecycle: a daemon thread started from the Flask app process itself** (`create_app`, no
   separate process to launch or keep in sync with config) — the same "background work lives
   inside the request-serving process" posture `run_in_background` (`src/app/api/tasks.py`)
   already established for one-shot ingestion jobs, extended here to a long-running poll loop.

Engineering details this decision also settles, not asked of Cleo directly but required for the
above four points to be implementable, decided by the same reasoning already applied elsewhere in
this corpus:

- **Settle rule**: a file is only considered for ingestion once its mtime is older than one full
  `poll_interval_seconds` — a dependency-free debounce against picking up a file mid-write/copy.
- **New config section** (`src/app/config/`, same pattern as `TaskStateConfig`/`RetrievalConfig`):
  `folder_watch.enabled` (default `false` — opt-in; no existing installation's behavior changes
  without deliberate action), `poll_interval_seconds` (default `30`), `inbox_dirname` (default
  `"_inbox"`), `processed_dirname` (default `"processed"`).
  No new `PEKOPEKO_*` env var — same asymmetry ADI-010 already accepts for options that don't need
  process-level override.
- **Folder creation**: `_inbox/`/`_inbox/processed/` are created on demand per domain, not
  required to pre-exist — the vault is user-managed (ADI-004), the watcher must not require the
  user to hand-create plumbing folders first.
- **Exclusions**: dotfiles and the `processed/` subfolder itself are never scan candidates.
- **Failure after dispatch**: since the move to `processed/` happens at dispatch time, not at
  ingestion completion, a task that later fails leaves its source file already in `processed/`.
  Recovery is manual — move the file back into `_inbox/` to retry. No automatic retry in V1,
  matching ADI-005's own stated fallback: "if task state is ever lost, the task must be
  resubmitted", never a silent, automatic redo.

## Alternatives considered

- **Real-time OS-level watcher (e.g. Python `watchdog`).** Rejected: adds a dependency and
  cross-platform event-semantics differences (including over network-synced folders, relevant
  given ADI-004's Obsidian-sync context) to buy a latency improvement no use case here needs.
- **Status quo — manual trigger only.** Rejected: this is precisely the gap this ADR exists to
  close.
- **A single global inbox, domain inferred some other way (subfolder-per-domain under one root,
  or a filename convention).** Rejected in favor of one inbox *inside* each domain: it keeps
  Domain Isolation's path-prefix enforceability intact with zero extra disambiguation logic,
  mirroring ADI-012's decision to keep `<domain>` a hard, unedited path prefix.
- **Leave the file in `_inbox/` and rely on TASK-001d's duplicate detection to skip it on later
  polls.** Rejected: forces a hash/compare pass over every file in the inbox on every tick
  indefinitely, strictly more I/O and more fragile than simply removing an already-dispatched
  file from the watched set via a move.
- **A separate standalone watcher process/script**, decoupled from the API server. Rejected:
  adds an operational burden (a second process to start, stop, and keep pointed at the same
  config) for no benefit a single daemon thread inside the existing process doesn't already give.

## Consequences

- `src/app/config/schema.py`/`loader.py` gain an additive `FolderWatchConfig` section, defaulting
  to `enabled: false` — no behavior change for any existing deployment until a user opts in.
- `src/app/api/app.py` (`create_app`) gains a conditional startup hook that launches the poll
  loop only when `folder_watch.enabled` is true.
- No change to `ingest_source`, `create_task_state`, or any of their existing callers/contracts —
  the watcher is a new caller, not a new code path inside ingestion itself.
- The Ingestion Logs screen (TASK-009, `completed`) needs no change: watcher-dispatched tasks flow
  through the exact same task-state mechanism as manually-dispatched ones and render identically.
- **TASK-001f** is the satellite ticket implementing this ADR — additive to TASK-001, following
  the same non-breaking posture already used by TASK-001a/b/c/d/e, since this is a new trigger
  path onto an existing entry point, not a change to extraction/parsing contracts.
