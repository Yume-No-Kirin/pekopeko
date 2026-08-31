# TASK-001b: Task Event Log for Ingestion and Extraction (V1)

- **Status**: completed

## Objective

Extend `TaskState` in both `ingestion/task_state.py` and `extraction/task_state.py`
(TASK-001 and TASK-003, both `completed`) with a persisted, timestamped list of processing
events per task, so the "Logs d'ingestion complets" section of
`specs/ux-design/pekopeko-proposal-detail.html` (and the "Voir logs"/"Voir erreur" actions
of `specs/ux-design/pekopeko-ingestion.html`) can render real step-by-step data instead of
being dropped. Today `TaskState` only carries a single `status` value and a single nullable
`error` string — no record of the intermediate steps a mockup viewer would expect to
inspect. Satellite ticket, letter-suffixed off TASK-001, to keep TASK-001's/TASK-003's own
historical records and acceptance-criteria numbering stable (same convention as TASK-001a).

## Binding context (references, not duplicated here)

- `specs/tasks/completed/TASK-001-data-ingestion.md` / `TASK-003-...md`: current `TaskState`
  minimum fields (`task_id, source_path, domain, status, started_at, completed_at, error,
  source_id, proposal_ids`) — this ticket adds to that shape, doesn't replace it.
- ADI-005 (sync-vs-async, Accepted): task state is local, per-device, non-canonical — loss
  of it is safe (resubmit the attempt). This ticket's new `events` field inherits that same
  placement/durability posture, nothing here becomes canonical.
- Module independence discipline (TASK-002's "Indépendance entre modules", reapplied by
  TASK-004/TASK-007 to `ingestion/task_state.py` and `extraction/task_state.py` as two
  separate mirrored edits, no cross-import): this ticket follows the same shape — two
  separate, symmetric edits, `extraction/` never imports `ingestion/`.
- `specs/ux-design/pekopeko-proposal-detail.html`, "Logs d'ingestion complets": timestamped
  entries (`[2026-08-25 14:20:12.345] INFO — Démarrage de l'ingestion...`, etc.) with a
  `details` block — the concrete target shape.
- `specs/tasks/backlog/TASK-009-ingestion-logs-screen.md`,
  `specs/tasks/backlog/TASK-011-proposal-detail-screen.md`: both depend on this ticket for
  their log-detail sections.

## Scope

1. New shared shape (duplicated per module, not imported across — same convention as
   `TaskState` itself today): a `TaskEvent` with `timestamp` (ISO 8601), `level` (one of
   `info`, `success`, `warning`), `message` (str), `details` (optional dict, free-form
   key/value pairs for the same kind of context the mockup shows — e.g. `task_id`,
   `domain`, `content_hash`).
2. `TaskState` gains `events: list[TaskEvent]` (default empty list), serialized the same
   way as the rest of `TaskState.to_dict()`/`from_dict()` — `from_dict()` tolerates a
   missing `events` key (treats it as `[]`) so `TaskState` files already on disk from
   before this ticket still load without error.
3. A new helper per module, `append_task_event(task_state, state_dir, level, message,
   details=None)`, appends one `TaskEvent` to `task_state.events` and persists the updated
   `TaskState` (reuses the existing `save`/`update_task_state` write path — no new file
   format).
4. `ingestion/pipeline.py`'s `ingest_source` and `extraction/pipeline.py`'s `extract_source`
   call `append_task_event(...)` at each already-existing pipeline step boundary: task
   started, source read, duplicate check result, source written, provider call started,
   provider call finished (success or failure), each Proposal written, task completed
   (or failed). This is instrumentation only — no change to what each step actually does,
   only that it now also records that it happened.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Purely additive: no change to `ingest_source`'s/`extract_source`'s public signatures, no
  change to any existing `TaskState` field's meaning.
- Events are append-only for the lifetime of one task attempt — no editing/removing a past
  event, matching the read-only "audit trail" posture the project already takes for
  `history/` snapshots elsewhere (TASK-006).
- No new HTTP endpoint in this ticket — `events` becomes visible over HTTP automatically
  once TASK-007's `list_task_states`/`load_task_state` JSON serialization
  (`src/app/api/serialization.py`) reflects the full `TaskState.to_dict()`, which already
  includes whatever keys `to_dict()` returns — no `api/` code change required here.
- No structured event taxonomy/enum beyond the 3-level `info`/`success`/`warning` — matches
  the 3 CSS classes (`info`/`success`/`warning`) already present in the mockup, nothing
  more granular invented.
- `details` values must be JSON-serializable primitives/dicts (matching the existing
  `TaskState.save()` `json.dump` call) — no arbitrary Python objects.

## Requirements

- Python only (ADI-007). No new dependency.
- No git usage (project-wide constraint).
- All directory/file writes reuse the existing atomic-enough `TaskState.save()` path — no
  new write mechanism introduced (this ticket doesn't change TASK-001's/TASK-003's write
  safety posture, only what's included in the JSON payload).

## Constraints

- No cross-import between `ingestion/task_state.py` and `extraction/task_state.py` — two
  separate, mirrored edits.
- No retroactive backfill of `events` on `TaskState` files already on disk — `from_dict()`
  simply defaults to `[]` for those.
- No change to the meaning of `status`/`error` — `events` is additive detail alongside
  them, not a replacement.
- No unbounded event growth concern in scope (a single ingestion/extraction attempt has a
  small, fixed number of steps — no pagination/truncation logic needed for `events` itself).

## Files/modules concerned

- `ingestion/task_state.py` — `TaskEvent`, `TaskState.events`, `append_task_event`.
- `extraction/task_state.py` — mirrored `TaskEvent`, `TaskState.events`,
  `append_task_event` (separate, independent implementation).
- `ingestion/pipeline.py` — `ingest_source` calls `append_task_event` at each step.
- `extraction/pipeline.py` — `extract_source` calls `append_task_event` at each step.
- `tests/ingestion/`, `tests/extraction/` — new tests for event sequencing on success and
  on simulated failure, plus a `from_dict`-tolerates-missing-`events`-key regression test.

## Dependencies

Depends on TASK-001 and TASK-003 (both `completed`) as the tickets it extends. Independent
of TASK-005/TASK-006/TASK-007 as code (TASK-007's API layer surfaces `events` for free once
this ticket lands, but doesn't need its own changes to do so — see V1 scope decisions).

## Acceptance criteria

1. A successful `ingest_source` call produces a `TaskState.events` sequence whose messages
   correspond, in order, to the real steps executed (start, source read, dedup check,
   source written, provider call, N Proposal writes, task completed) — verified against a
   fixture source with a stub `Provider`.
2. A successful `extract_source` call produces an equivalent, independently-implemented
   `events` sequence for its own steps.
3. A simulated provider failure (both pipelines) appends a `warning`-level event describing
   the failure before the task is marked `failed` — no exception swallowed silently without
   a corresponding event.
4. A duplicate-source ingestion (`skipped_duplicate`) appends an event describing the
   duplicate detection instead of the full success sequence.
5. Loading a `TaskState` JSON file written before this ticket (no `events` key present) via
   `from_dict()` succeeds and yields `events == []` — no `KeyError`/exception.
6. `events` entries are JSON-serializable and round-trip correctly through
   `save()`/`load_task_state()` (timestamp, level, message, details all preserved).
7. `ingest_source`'s and `extract_source`'s public parameter lists are unchanged (verified
   via `inspect.signature`).
8. All pre-existing `tests/ingestion/` and `tests/extraction/` tests pass unmodified (same
   29/31 and 44/44 baselines as prior verification records).

## Testing requirements

`pytest`, `tmp_path`, no real network calls, stub `Provider` fixtures already established
by TASK-001/TASK-003 test suites. Minimum: one test per acceptance criterion above (8
total) per module where applicable (ingestion and extraction each get their own coverage
for criteria 1/3/4). Coverage discipline (≥80%) applies to the touched portions of both
`ingestion/` and `extraction/`.

## Out of scope

- Any new HTTP endpoint (covered automatically via TASK-007's existing serialization, see
  V1 scope decisions).
- Event pruning/retention policy, pagination of `events` itself.
- A shared/imported `TaskEvent` type between `ingestion/` and `extraction/` — kept as two
  independent, mirrored definitions per this project's module-independence convention.
- Any GUI — TASK-009/TASK-011 consume this ticket's output, implemented separately.

## Implementation notes

- Both `ingestion/task_state.py` and `extraction/task_state.py` gained an identically
  shaped but independently defined `@dataclass TaskEvent` (`timestamp`, `level`, `message`,
  `details: Optional[Dict]`) with its own `to_dict()`/`from_dict()`, plus a `TaskState.events`
  list field.
- `TaskState.to_dict()` serializes `events` via `[e.to_dict() for e in self.events]`.
  `TaskState.from_dict()` pops `'events'` (default `[]`) before calling `cls(**data)`,
  converting each raw dict back to a `TaskEvent` — this is what makes AC5 (a pre-ticket
  `TaskState` JSON file with no `events` key) work: the pop default handles it with no
  separate branch.
- `append_task_event(task_state, state_dir, level, message, details=None)` was added to
  both modules, appending one `TaskEvent` (timestamped via `datetime.now().isoformat()`)
  and persisting through the existing `update_task_state`/`save()` path — no new write
  mechanism.
- Both modules' `__init__.py` now export `TaskEvent`/`append_task_event` alongside
  `TaskState`.
- `ingest_source`/`extract_source` gained `append_task_event(...)` calls at each step
  boundary listed in Scope item 4, added alongside (not replacing) the pre-existing
  `update_task_state` calls at status transitions. The duplicate-detection branch stops
  after its one event (`"Duplicate source detected, skipping ..."`) instead of emitting
  the rest of the sequence, satisfying AC4. `extract_source`'s three proposal-writing loops
  (entities/events/relationships) each tag their `"Proposal written"` event's `details`
  with `proposed_item_type`. Every failure path (provider exception, proposal-write
  exception, and each pipeline's outer catch-all `except Exception`) appends a
  `"warning"`-level event describing the failure before `task_state.status` is set to
  `"failed"`, so AC3's "no exception swallowed silently without a corresponding event"
  holds for all three failure surfaces per pipeline, not just the provider-call one.
- Neither pipeline's public signature changed (`ingest_source`: `vault_root, domain,
  source_path, provider, state_dir`; `extract_source`: same) — verified by
  `inspect.signature` regression tests (AC7); `ingest_source`'s test already existed
  (TASK-001a), `extract_source`'s is new here.
- New tests: `tests/ingestion/test_task_state.py` (new file, mirrors the existing
  `tests/extraction/test_task_state.py`) plus additions to both `test_task_state.py` files
  and both `test_pipeline.py` files — event-sequence-on-success (AC1/AC2), provider-failure
  warning event (AC3), duplicate-sequence (AC4), `from_dict` legacy-dict regression (AC5),
  save/load round-trip (AC6), signature regression (AC7). Two additional ingestion-only
  tests (`test_proposal_write_failure_appends_warning_event`,
  `test_unregistered_extension_appends_failure_event_via_outer_handler`) were added beyond
  the ticket's minimum to close a coverage gap on `ingestion/pipeline.py`'s two remaining
  instrumented failure branches (extraction's equivalent branches were already covered by
  its existing test suite, so no extraction-side equivalent was needed).

## Verification record (2026-08-31)

Implemented by Claude (this session). Per this project's verification discipline: code
(`src/app/ingestion/`, `src/app/extraction/`, `src/tests/ingestion/`,
`src/tests/extraction/`) was copied to an isolated scratch directory outside the repo
(`.../scratchpad/task001b_verify/`) and both test suites re-run independently there rather
than trusting the in-repo run alone. A hand-written manual reproduction script ran a real
`ingest_source()` call end-to-end (stub `Provider`, no network) and printed the written
`TaskState` JSON file in full for by-eye inspection of the `events` array shape. `git
stash`/`git stash pop` before/after was deliberately **not** used for this comparison (as
TASK-001a's record did): this repo's working tree already carried other uncommitted,
legitimate in-progress changes (TASK-001a/TASK-004-related files) at the start of this
session, and stashing would have disturbed that unrelated work rather than isolating this
ticket's own diff. The isolated-copy comparison serves the same purpose without that risk.

Each acceptance criterion checked individually:

- `[PASS]` AC1 (successful `ingest_source` produces an ordered `events` sequence matching
  the real steps executed) -- `test_successful_ingestion_event_sequence` asserts the exact
  ordered message list (`Ingestion task started` -> `Source content read` -> `No duplicate
  found...` -> `Source file written` -> `Provider extraction call started` -> `...finished`
  -> `Proposal written` x2 -> `Ingestion task completed`) against a stub provider returning
  2 assertions. Passes in-repo and in the isolated copy. The manual reproduction script's
  printed JSON (1 assertion) shows the same 8-step shape by eye.
- `[PASS]` AC2 (equivalent, independently-implemented sequence for `extract_source`) --
  `test_successful_extraction_event_sequence` asserts the analogous 10-message sequence
  (3 proposal writes: entity/event/relationship, each tagged via
  `details["proposed_item_type"]`) against `FakeProvider`. Passes in both runs.
- `[PASS]` AC3 (provider failure appends a `warning` event before `status == "failed"`, no
  exception swallowed silently) -- `test_provider_failure_appends_warning_event_before_failed`
  (both pipelines) confirms exactly one `warning` event, message describing the failure,
  positioned as the last event before the persisted `status` is `"failed"`. Two further
  ingestion-only tests (`test_proposal_write_failure_appends_warning_event`,
  `test_unregistered_extension_appends_failure_event_via_outer_handler`) confirm the same
  holds for the other two failure surfaces (proposal-write exception, outer catch-all).
  Extraction's equivalent branches were already exercised by pre-existing tests
  (`test_relationship_endpoints_fewer_than_two_raises_before_write`,
  `test_unregistered_extension_fails_via_outer_handler`), confirmed via the coverage run
  below rather than needing new extraction-side tests. All pass in both runs.
- `[PASS]` AC4 (duplicate ingestion appends a duplicate-describing event instead of the
  full success sequence) -- `test_duplicate_ingestion_event_sequence` /
  `test_duplicate_extraction_event_sequence` assert the shorter 3-message sequence ending
  in `"Duplicate source detected, skipping ..."` for the second, duplicate call. Both pass
  in both runs.
- `[PASS]` AC5 (`from_dict` tolerates a missing `events` key, yields `events == []`, no
  exception) -- `test_from_dict_tolerates_missing_events_key` (both modules) constructs a
  hand-built legacy dict with no `events` key and asserts a clean load. Both pass in both
  runs.
- `[PASS]` AC6 (`events` entries JSON-serializable, round-trip through
  `save()`/`load_task_state()` with timestamp/level/message/details preserved) --
  `test_events_round_trip_through_save_and_load` (both modules) plus the manual
  reproduction script's printed JSON (valid UTF-8, no BOM, no mojibake, matches the
  in-memory event exactly). Both pass in both runs.
- `[PASS]` AC7 (`ingest_source`/`extract_source` public parameter lists unchanged) --
  `test_ingest_source_signature_unchanged` (pre-existing, TASK-001a) and the new
  `test_extract_source_signature_unchanged`, both via `inspect.signature`. Both pass in
  both runs.
- `[PASS]` AC8 (all pre-existing `tests/ingestion/`/`tests/extraction/` tests pass
  unmodified) -- in-repo: 43/45 `ingestion` (41 pre-existing/pre-ticket-adjacent + new;
  same 2 pre-existing, unrelated failures as TASK-001a/TASK-004's own records) and 51/51
  `extraction`. Isolated-copy run: identical figures, both suites. No pre-existing test
  file was edited beyond the two `test_task_state.py`/`test_pipeline.py` additions this
  ticket's own scope calls for.
- `[PASS]` Test coverage on touched files -- working tree and isolated copy report
  identical figures: `extraction/pipeline.py` 100%, `extraction/task_state.py` 100%,
  `ingestion/pipeline.py` 99%, `ingestion/task_state.py` 97% (the two remaining uncovered
  ingestion lines are the pre-existing, untouched `process_source` backward-compat wrapper
  and `load_task_state`'s missing-file branch, neither touched by this ticket). All well
  above the project's >=80% requirement.

**Pre-existing failures, confirmed unrelated to this ticket** (same two documented in
TASK-001a's/TASK-004's verification records, re-confirmed here via the isolated-copy run):
`tests/ingestion/test_comprehensive.py::test_acceptance_criteria_compliance` and
`tests/ingestion/test_pipeline.py::test_import_isolation`, both failing on a hardcoded
`Path("app/ingestion/pipeline.py")` relative-path read that doesn't match this repo's
actual run-from-repo-root convention, regardless of this ticket. Left untouched per this
ticket's scope (no unrelated cleanup).

**Honesty note on independence**: this verification was performed by the same Claude
session that wrote the implementation, not by a separate reviewer or model (same caveat as
TASK-001a/002/003/004's verification records). It does follow the isolated-copy-and-
independently-rerun discipline the project asks for, plus a manual by-eye reproduction
script beyond just re-running pytest, but it is not the same strength of evidence as an
independent second reviewer.
