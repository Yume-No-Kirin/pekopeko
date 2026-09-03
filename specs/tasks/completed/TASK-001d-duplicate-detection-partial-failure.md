# TASK-001d: Duplicate Detection Ignores Partial-Failure Retries (V1)

- **Status**: completed (2026-09-03)

## Objective

Fix a real bug found in usage (2026-09-03, Cleo): after a source is written to disk but
the extraction step that follows it fails (provider error), every subsequent retry on the
same source is silently swallowed as `skipped_duplicate` — the provider is never called
again, with no error surfaced to the user. Separately, when a retry *is* forced (e.g. by
manually removing the stale source file), the Validation screen's group status badge can
end up showing the stale `failed` status from the very first attempt instead of the
outcome of the most recent one. Satellite ticket, letter-suffixed off TASK-001 (same
convention as TASK-001a/b/c), extending TASK-001 and TASK-003 with symmetric, independent
edits and fixing a bug in TASK-010's already-`completed` frontend code.

## Binding context (references, not duplicated here)

- `specs/tasks/completed/TASK-001-data-ingestion.md` / `TASK-003-...md`: current
  `ingest_source`/`extract_source` duplicate-detection contract this ticket changes —
  today, "duplicate" is decided purely by `Path.exists()` on the source file.
- `specs/tasks/completed/TASK-001b-task-event-log.md`: the module-independence convention
  this ticket follows (`ingestion/pipeline.py` and `extraction/pipeline.py` get two
  separate, mirrored edits, never a cross-import), and the existing `append_task_event`
  helper this ticket adds new event messages through.
- ADI-005 (sync-vs-async, Accepted): task state is local, per-device, non-canonical — its
  loss means "resubmit the task," never "corrupt the canonical." This is the reasoning
  behind this ticket's chosen fix (query `list_task_states` for a prior `completed` task,
  rather than scanning `proposals/` for existing Proposals referencing the source): if
  task state is ever lost, the pipeline's worst-case fallback is exactly the safe ADI-005
  outcome — treat the source as not-yet-successfully-processed and retry — never corrupted
  canonical data.
- `specs/tasks/completed/TASK-010-validation-screen.md`: the `Validation.jsx` code this
  ticket fixes (`fetchGroups()`'s `taskStatusBySourceId` construction) — no change to that
  ticket's own scope or acceptance criteria, this is a bug fix in its delivered code.
- `specs/tasks/backlog/TASK-001c-zero-output-extraction-failure.md` / ADI-011: a related
  but **distinct** bug, already ticketed and blocked on Cleo's confirmation of ADI-011.
  TASK-001c is about a provider silently returning zero results for non-empty content;
  this ticket is about a provider *raising an exception* after the source was already
  written. Do not conflate the two — this ticket does not depend on or block on TASK-001c.

## Scope

### 1. Backend — duplicate check based on prior success, not file existence

Applies independently to both `ingest_source` (`ingestion/pipeline.py`) and
`extract_source` (`extraction/pipeline.py`), same shape, no shared code between them
(same discipline as TASK-001b).

- Today: `if existing_source_path.exists(): → skipped_duplicate`.
- New: `if existing_source_path.exists() AND list_task_states(state_dir)` contains at
  least one **other** task for this `source_id` with `status == "completed"` →
  `skipped_duplicate` (unchanged observable behavior for the real-duplicate case).
- If the source file exists but no prior `completed` task is found for this `source_id`
  (every prior attempt for it is `failed`, still `running`/`pending`, or no task state
  exists at all for it — e.g. lost/never-written task state): **do not skip**. Reuse the
  already-written source file as-is (never rewrite it — content is identical by
  construction of the hash-based `source_id`), append a new task event describing the
  reuse, and continue straight into the provider-extraction step as a normal attempt.
- `append_task_event` gets a new distinct message for this third case ("Existing source
  reused, retrying extraction" or equivalent), so the three now-possible paths (real
  duplicate skip / first-ever write / retry-reusing-existing-source) are each
  individually visible in the task's `events` log (TASK-001b), not merged into one
  ambiguous message.

### 2. Frontend — keep the most recent task status per source, not the last one iterated

`Validation.jsx`'s `fetchGroups()` builds `taskStatusBySourceId` by calling `.set()`
unconditionally for every task returned by `listIngestions`. Each domain's task list is
already sorted `started_at` descending by the API (`sort_by_recency`,
`src/app/api/routes_ingestion.py`), so the *first* task encountered for a given
`source_id` while iterating forward is always the most recent one. The current
unconditional `.set()` instead lets the *last*-iterated (= oldest) task win, since it
overwrites every earlier `.set()` call.

- Fix: only set the map entry the first time a `source_id` is seen —
  `if (task.source_id && !taskStatusBySourceId.has(task.source_id)) { ...set... }`.
- Add a one-line comment at the call site stating this relies on the API's
  `started_at`-descending sort order, so a future change to that sort order doesn't
  silently reintroduce this bug.

### Known limitation (explicit — flag, don't silently omit)

If the failed first attempt had already written *some* Proposals before erroring out
mid-loop (a provider call that fails partway through returning results, or a write
failure on one Proposal among several already written — both pipelines' existing
per-item write loops can do this), a retry under this ticket reruns extraction from
scratch and can produce duplicate Proposals for the items already written by the failed
attempt. Idempotent Proposal-level deduplication on retry is out of scope for this ticket
— the bug Cleo reported is a provider call failing before any Proposal is written, which
this ticket's fix fully resolves; the partial-proposal-write case is a narrower,
pre-existing edge case left for a future ticket if it becomes a real problem in practice.

## Requirements

- Python only for the backend half (ADI-007), plain JS/JSX for the frontend half (no new
  dependency either side).
- No git usage (project-wide constraint).
- No change to `TaskState`'s persisted file format or write path beyond the new event
  message text (no new field).

## Constraints

- No cross-import between `ingestion/pipeline.py` and `extraction/pipeline.py` — two
  separate, mirrored edits, same as every prior TASK-001/TASK-003 satellite.
- No change to `ingest_source`'s / `extract_source`'s public parameter lists.
- No change to the meaning of any existing `TaskState.status` value or to the real
  (non-partial-failure) duplicate-skip behavior — verified by acceptance criterion 2
  below.
- The frontend fix touches only `Validation.jsx`'s `fetchGroups()` — no change to
  `SourceGroupHeader.jsx`, `TaskStatusBadge.jsx`, or `api/tasks.js`.

## Files/modules concerned

- `src/app/ingestion/pipeline.py` — `ingest_source`'s duplicate-check branch.
- `src/app/extraction/pipeline.py` — `extract_source`'s duplicate-check branch
  (independent, mirrored implementation).
- `frontend/src/pages/Validation.jsx` — `fetchGroups()`'s `taskStatusBySourceId`
  construction.
- `src/tests/ingestion/`, `src/tests/extraction/` — new tests for retry-after-failure and
  regression tests for the real-duplicate case.
- `frontend/src/pages/Validation.test.jsx` — new test for status-by-most-recent-task.

## Dependencies

Depends on TASK-001 and TASK-003 (both `completed`) as the tickets it extends, and on
TASK-010 (`completed`) for the file it fixes. Independent of TASK-001c/ADI-011 (see
Binding context) — implementable and mergeable regardless of ADI-011's status.

## Acceptance criteria

1. A first `ingest_source` attempt that fails after the source file is written (provider
   raises) followed by a second attempt on the same source content calls the provider
   again (no skip) and, if the provider succeeds this time, produces Proposals and ends
   with `status == "completed"`.
2. A genuine duplicate — a prior attempt on the same source content already reached
   `status == "completed"` — still returns `skipped_duplicate` without calling the
   provider again. Non-regression of current behavior.
3. Criteria 1 and 2 hold independently for `extract_source` (its own test suite, its own
   stub provider).
4. The reused-source-on-retry path (criterion 1) does not rewrite `sources/<id>/<id>.md`
   — content/mtime unchanged from the first, failed attempt's write.
5. `append_task_event`'s log for a retry-after-failure attempt contains a distinct event
   message identifying it as a retry reusing an existing source, different from both the
   real-duplicate-skip message and the fresh-write message.
6. In `Validation.jsx`, a group whose `source_id` has multiple ingestion tasks (e.g. an
   older `failed` one and a newer `completed` one, injected in a non-trivial order into
   the test fixture — not already sorted the "convenient" way) displays the status of the
   most recent task by `started_at`, not the oldest.
7. `ingest_source`'s and `extract_source`'s public parameter lists are unchanged
   (`inspect.signature` regression tests, same discipline as TASK-001b AC7).
8. All pre-existing `tests/ingestion/`, `tests/extraction/`, and `Validation.test.jsx`
   tests pass unmodified.

## Testing requirements

`pytest` with `tmp_path`, no real network calls — stub `Provider` fixtures already
established by TASK-001/TASK-003 suites, extended with one that fails on its first call
and succeeds on a second call against the same content. Vitest for the frontend criterion
(criterion 6), with task fixtures deliberately not pre-sorted by recency so the test
actually exercises the fix rather than passing by coincidence. Minimum one test per
acceptance criterion. Coverage discipline (≥80%) applies to the touched portions of
`ingestion/`, `extraction/`, and `Validation.jsx`.

## Out of scope

- Idempotent deduplication of Proposals partially written before a mid-loop failure (see
  Known limitation above).
- TASK-001c / ADI-011 (zero-output provider contract) — separate, already-ticketed bug,
  not addressed here.
- Any change to how `listExtractions`-derived task status would feed a similar group
  display for entity/event/relationship proposals — out of scope of TASK-010/Validation
  (assertion-only), would belong to TASK-012 if ever needed there.
- Performance/indexing of source→task lookups for very large `state_dir`s — `list_task_states`
  already exists and is reused as-is; no new index introduced.

## Implementation notes

- `ingestion/pipeline.py::ingest_source` and `extraction/pipeline.py::extract_source`
  restructured their duplicate-check `if existing_source_path.exists(): ... else: ...`
  two-branch shape into a three-branch shape: real-duplicate-skip (prior `completed`
  task found via `list_task_states`, unchanged behavior) / reuse-and-retry (file exists,
  no prior `completed` task — new) / fresh-write (file doesn't exist, unchanged
  behavior). `list_task_states` added to each module's existing import from
  `.task_state`. No other code in either function needed to change — the
  extraction/provider-call section downstream already only depends on
  `content`/`source_id`/`task_state`, all set identically regardless of which of the
  three branches ran.
- The "other task" filter is `s.source_id == source_id and s.task_id != task_state.task_id
  and s.status == "completed"` — `task_id != task_state.task_id` is a redundant-but-cheap
  safety guard (the current task's own state is saved with `status="running"` and
  `source_id=None` at the point this check runs, so it could never spuriously match on
  its own, but excluding it by id keeps the intent explicit).
- Both `write_source_file`/`storage.write_source_file` were already atomic, unconditional
  writes with no existence check inside them — satisfying AC4 required only skipping the
  call entirely in the reuse-and-retry branch, not modifying either write function.

## Verification record

Implemented and verified by Claude (2026-09-03), same session, following the project's
verification discipline (AGENTS.md): reproduced independently rather than trusting a
single test run.

- `pytest src/tests/ingestion/` (62 tests total, 4 new for this ticket): 60/62 pass.
  The 2 failures (`test_pipeline.py::test_import_isolation`,
  `test_comprehensive.py::test_acceptance_criteria_compliance`) are **pre-existing and
  unrelated** — confirmed by `git stash` (removing this ticket's edits) and re-running:
  both fail identically on the stashed (pre-ticket) code. `test_import_isolation` fails
  on a relative-path assumption (`Path("app/ingestion/pipeline.py")`) unrelated to
  duplicate detection; `test_acceptance_criteria_compliance` (TASK-001's own original
  test) calls `ingest_source` a third time on the same content expecting `"failed"`, but
  every prior code version (both before and after this ticket) treats a second-or-later
  call on an already-written source as `Path.exists()`-driven — pre-ticket that meant an
  unconditional skip regardless of provider, so the assertion never held even before this
  session. Flagged here, not silently worked around; out of this ticket's declared scope
  to fix (not touched).
- `pytest src/tests/extraction/` (65 tests total, 4 new): 65/65 pass, no pre-existing
  failures in this suite.
- Coverage on the two touched files: `src/app/ingestion/pipeline.py` 99% (one pre-existing
  uncovered line, an unrelated legacy wrapper function, line 236, untouched by this
  ticket); `src/app/extraction/pipeline.py` 100%.
- `cd frontend && npx vitest run --coverage`: 45/45 tests pass (1 new in
  `Validation.test.jsx`, "TASK-001d AC6: ..."), no regressions in any other page.
  `Validation.jsx` itself 96.5% line / 92.64% branch coverage; project-wide coverage
  97.77%, both well above the 80% threshold.
- Manual end-to-end reproduction script, run against an isolated copy of `src/`
  (`scratchpad/task001d_manual_repro.py`, not committed): for both `ingest_source` and
  `extract_source` independently — attempt 1 (provider raises after source write) fails
  and leaves the source file on disk; attempt 2 (retry, same content) calls the provider
  again and completes, with the source file's content and mtime byte-for-byte unchanged
  from attempt 1; attempt 3 (now a genuine duplicate, since attempt 2 reached
  `completed`) skips without calling the provider again. Inspected each attempt's
  `TaskState.events` by eye: attempt 1 shows `"No duplicate found, continuing
  ingestion/extraction"` + `"Source file written"`, attempt 2 shows `"Existing source
  reused, retrying ingestion/extraction"` (and no `"Source file written"`), attempt 3
  shows `"Duplicate source detected, skipping ingestion/extraction"` — the three paths
  are each distinctly visible, satisfying AC5.
- Acceptance criteria checked one by one against the list above: AC1 (retry calls
  provider again, completes) — manual repro + `test_retry_after_failure_calls_provider_
  again_and_completes` (both pipelines). AC2 (genuine duplicate still skips) —
  `test_duplicate_still_skips_after_prior_completed_task` (both pipelines) +
  pre-existing `test_duplicate_detection` (both, unmodified, still passing). AC3 (both
  pipelines independently) — mirrored, separate test modules, no shared code. AC4 (no
  rewrite) — `test_retry_does_not_rewrite_source_file` (both pipelines) + manual repro
  byte-for-byte content/mtime check. AC5 (distinct event message) —
  `test_retry_after_failure_event_message_distinct` (both pipelines) + manual repro.
  AC6 (frontend, most-recent-task badge) — new Vitest test with a deliberately
  API-realistic (started_at-descending) two-task fixture, which is the order that
  actually discriminates the pre-fix "last wins" bug from the fix's "first wins"
  behavior (a fixture in the opposite order would let the old bug pass by
  coincidence — the ordering choice itself was reasoned through explicitly, not just
  copied from the ticket's own hint). AC7 (signature unchanged) — pre-existing
  `test_ingest_source_signature_unchanged`/`test_extract_source_signature_unchanged`,
  unmodified, still passing. AC8 (pre-existing tests pass unmodified) — full suite runs
  above, both languages.
- Limit, same as every prior ticket in this project: verification performed by the same
  Claude session that implemented the change, not by a second independent reviewer.
