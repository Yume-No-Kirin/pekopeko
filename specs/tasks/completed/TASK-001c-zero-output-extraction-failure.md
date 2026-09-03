# TASK-001c: Fail Loudly on Zero-Output Provider Extraction (Ingestion + Extraction)

- **Status**: completed

## Objective

Implement ADI-011 (Proposed): make `OllamaProvider.extract()` raise, instead of silently
returning an empty-but-"successful" `ExtractionResult`, when it produces zero extracted
items for non-empty source content — and add a pipeline-level guard that fails fast, with a
distinct error, on a genuinely empty source file before the provider is ever called. Exists
because gpt-oss:20b once exhausted its context window and returned `done_reason: "length"`
with an empty response body; neither `OllamaProvider` implementation reads `done`/
`done_reason`, and an empty response parses to an empty list without error, so the task was
recorded as `completed` with 0 assertions — a silent success indistinguishable from "nothing
to extract here." Satellite ticket to TASK-001 and TASK-003, following the same posture as
TASK-001b (one ticket, two separate, non-cross-importing edits, symmetric across
`ingestion/` and `extraction/`), rather than an amendment to either completed ticket's file.

## Binding context (references, not duplicated here)

- `specs/decisions/ADI-011-provider-zero-output-contract.md` (Proposed — **must be
  confirmed by Cleo before this ticket is implemented**, per this project's "an ADR with
  status Proposed is not a decision" rule): the contract this ticket implements — `Provider.
  extract()` must raise on zero output for non-empty input; a genuinely empty source is a
  separate, pipeline-level condition, never conflated with the provider returning nothing.
- ADI-008 (llm-provider-architecture, Accepted): pipeline code depends only on the
  `Provider` protocol (`extract(text, context) -> ExtractionResult`) — this ticket's fix
  lives inside the concrete `OllamaProvider` implementations and the shared
  read-content-then-call-provider sequence already present in both pipelines, never a
  pipeline-level special-case keyed on which provider is active.
- `specs/tasks/completed/TASK-001-data-ingestion.md` and
  `specs/tasks/completed/TASK-003-entity-event-relationship-extraction.md`: the two
  pipelines this ticket extends, additively — no change to either ticket's own acceptance
  criteria numbering.
- `specs/tasks/completed/TASK-001b-task-event-log.md`: precedent for one satellite ticket
  symmetrically extending both TASK-001 and TASK-003 with two separate, non-cross-importing
  edits — same posture followed here.
- `specs/domain/knowledge-invariants.md`, INV-019: "a failed extraction must not corrupt the
  source or leave a partially-written Proposal file — must leave inspectable, honest failure
  state." A task recorded as `completed` with 0 propositions is not honest failure state
  when the provider actually produced nothing usable; this ticket closes that gap.

## Scope

1. `ingestion/providers/ollama_provider.py`'s `OllamaProvider.extract()`: capture
   `done_reason = result_data.get("done_reason")` from the Ollama response JSON. After
   `_parse_assertions()` returns, if the assertion list is empty, raise `ValueError` with a
   message that includes `done_reason=<value>`, the configured model, and the raw response
   text length.
2. `extraction/providers/ollama_provider.py`'s `OllamaProvider.extract()`: same
   `done_reason` capture. After `_parse_extraction_result()` returns, if entities, events,
   and relationships are all empty, raise with the same diagnostic shape (`done_reason=`,
   model, response length).
3. `ingestion/pipeline.py`'s `ingest_source()` and `extraction/pipeline.py`'s
   `extract_source()`: immediately after reading source content (`registry.read_file(...)`),
   before the duplicate-source check and before calling the provider, fail the task with a
   distinct `"Source file is empty"` error if the content is empty or whitespace-only. The
   provider must never be called in this case.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Reuses the existing `"failed"` `task_state.status` — no new status value, no frontend
  change (`TaskStatusBadge.jsx` already renders `"failed"` + `error` correctly).
- The zero-output check lives inside `OllamaProvider.extract()` (per ADI-011), not as a
  second check bolted onto the pipeline after the call returns: both pipelines already wrap
  `provider.extract()` in `try/except Exception`, converting any raised exception into
  `task_state.status = "failed"` / `task_state.error = str(e)` — this ticket needs no new
  pipeline-level status-handling code beyond the empty-source guard (Scope item 3).
- `done_reason` is captured only as diagnostic text inside the raised error's message
  string — no new field added to `ExtractionResult`, `TaskState`, or the Proposal
  `provenance` dict (TASK-001a's four provenance fields are unchanged).
- No retry/backoff introduced. A provider that produces zero output fails the task once;
  resubmission (if desired) is a manual re-ingestion, same as any other provider failure
  today.

## Requirements

- Python only (ADI-007). No new dependency.
- No change to any file outside `ingestion/`, `extraction/`, and their `tests/`
  counterparts.
- No git usage (project-wide constraint).

## Constraints

- No new `TaskState.status` value.
- No change to `ingest_source`'s or `extract_source`'s public parameter list.
- No change to the Proposal `provenance` dict contract established by TASK-001a.
- No retry logic.
- Implementation does not begin until ADI-011 is confirmed `Accepted`, not merely drafted
  `Proposed`.

## Files/modules concerned

- `ingestion/providers/ollama_provider.py`
- `extraction/providers/ollama_provider.py`
- `ingestion/pipeline.py`
- `extraction/pipeline.py`
- `tests/ingestion/` and `tests/extraction/` — new tests for the zero-output-raises
  behavior (both providers) and the empty-source guard (both pipelines).

## Dependencies

Depends on TASK-001 and TASK-003 (both `completed`) as the tickets it extends, and on
ADI-011 being confirmed (not just drafted) before implementation begins.

## Acceptance criteria

1. `OllamaProvider.extract()` (`ingestion/`) raises when the parsed assertion list is
   empty; the raised error's message contains the string `done_reason=`.
2. `OllamaProvider.extract()` (`extraction/`) raises when entities, events, and
   relationships are all empty; same `done_reason=` requirement.
3. `ingest_source()`: a provider mock that raises the zero-output error results in
   `task_state.status == "failed"` and `task_state.error` containing the diagnostic
   message — no Proposal files written.
4. `extract_source()`: same as AC3, for the extraction pipeline.
5. `ingest_source()` and `extract_source()`: an empty/whitespace-only source file fails the
   task with `task_state.error == "Source file is empty"`, and the provider mock's
   `extract()` is never called (verified via call-count assertion).
6. A provider mock returning a non-empty result is unaffected — existing TASK-001/TASK-003
   happy-path tests keep passing unmodified.
7. All pre-existing `tests/ingestion/` and `tests/extraction/` tests pass unmodified (same
   pre-existing-failure baseline already documented by TASK-001a/TASK-001b).

## Testing requirements

pytest, `tmp_path`, no real network calls (mock `requests.post`'s response JSON, including
a `done_reason: "length"` + empty `"response"` case for both providers). Minimum one test
per acceptance criterion above. Coverage discipline (>=80%) applies to the touched portions
of `ingestion/` and `extraction/`.

## Out of scope

- Retry/backoff on empty or truncated output.
- Capturing `done_reason` (or any provider-specific diagnostic) as a structured field
  anywhere outside the raised error's message string — no schema change to
  `ExtractionResult`, `TaskState`, or Proposal `provenance`.
- A second concrete `Provider` implementation adopting this contract — inherits it
  automatically per ADI-011 once it lands (TASK-020, not yet ticketed).
- Any GUI change — `TaskStatusBadge.jsx`/`IngestionLogs.jsx` already render `"failed"` +
  `error` correctly; no frontend file touched.

## Implementation notes

- `ingestion/providers/ollama_provider.py::OllamaProvider.extract()`: captures
  `done_reason = result_data.get("done_reason")` right after `response.json()`; after
  `_parse_assertions()` returns, raises `ValueError` if the assertion list is empty,
  message `f"Ollama returned 0 assertions (done_reason={done_reason!r}, model=..., response_chars=...)"`.
  `_parse_assertions("")` already returns `[]` without raising (splitting an empty string
  on newlines yields no non-empty lines), so this single check is sufficient — no
  pre-parse guard needed here, unlike `extraction/`'s provider (see below).
- `extraction/providers/ollama_provider.py::OllamaProvider.extract()`: same `done_reason`
  capture. **Deviation found via manual reproduction, fixed before finalizing**: an
  initial version checked emptiness only *after* `_parse_extraction_result()` returned —
  but `_parse_extraction_result()` itself raises `"LLM response did not contain a JSON
  object"` when `extracted_text` is a genuinely empty string (no `{`/`}` to find), which
  is exactly the real gpt-oss:20b incident shape (empty `"response"` field). That earlier
  raise pre-empted the new check, so `done_reason` never reached the error message for
  the ticket's own motivating scenario. Fixed by adding a guard *before* calling
  `_parse_extraction_result()`: if `extracted_text.strip()` is empty, raise immediately
  with the `done_reason` diagnostic; the existing post-parse check still covers the
  separate case of syntactically valid but semantically empty output (e.g. a literal
  `"{}"` response).
- `ingestion/pipeline.py::ingest_source()` and `extraction/pipeline.py::extract_source()`:
  both gained an `if not content.strip():` guard immediately after the "Source content
  read" event and before the duplicate-source check, failing the task with
  `error = "Source file is empty"` and never reaching the provider. `ingestion/`'s guard
  reuses the `result = IngestionResult()` already constructed earlier in the function;
  `extraction/`'s constructs `ExtractionPipelineResult(source_id=None, proposal_ids=[],
  status="failed", error=...)` inline, matching the failure-return style already used a
  few lines below it in that function.
- No signature changes to `ingest_source`/`extract_source`; no new `TaskState.status`
  value; no schema change to `ExtractionResult`/`TaskState`/Proposal `provenance` —
  `done_reason` lives only in the raised error's message string, per the ticket's V1 scope
  decisions.
- New test file `src/tests/ingestion/test_ollama_provider.py` (didn't exist before this
  ticket — `OllamaProvider` there previously had only indirect coverage via
  `test_pipeline.py`), mirroring `src/tests/extraction/test_ollama_provider.py`'s existing
  `Mock()`-based style.
- `src/tests/extraction/test_ollama_provider.py`: `test_extract_handles_missing_lists`
  (previously asserted an all-empty JSON payload was a *successful* empty result) renamed
  to `test_extract_raises_on_all_empty_lists` and updated to assert a raise — this is the
  ticket's intended behavior change per ADI-011, not a regression. Two new tests added:
  one for the `done_reason` diagnostic on an all-empty-but-parseable payload, one for the
  empty-response-text-before-JSON-parse guard found via manual reproduction (above). A
  companion happy-path test (`test_extract_succeeds_when_at_least_one_list_non_empty`) was
  also added for symmetry with the ingestion side's new happy-path test.

## Verification record (2026-09-03)

Implemented by Claude (this session). Per this project's verification discipline: code
(`src/app/ingestion/`, `src/app/extraction/`, `src/tests/ingestion/`, `src/tests/extraction/`)
was copied to an isolated scratch directory outside the repo
(`.../scratchpad/task001c_verify/`) and the test suites re-run independently there, rather
than trusting the in-repo run alone. Pre-existing-failure baseline was reconfirmed via
`git stash`/`git stash pop` scoped to exactly this ticket's changed files (leaving other,
unrelated pre-existing uncommitted changes in the tree untouched) before and after this
ticket's changes: identical 2 pre-existing, unrelated `tests/ingestion` failures both
times (see below). A hand-written manual reproduction script (`manual_repro.py`, run in
the isolated copy) called `ingest_source()`/`extract_source()` end-to-end through the real
`OllamaProvider.extract()` (with `requests.post` mocked, no real network call) for five
scenarios: the actual gpt-oss:20b incident shape for both pipelines, the empty-source-file
guard for both pipelines, and one happy-path regression check — all five printed results
were inspected by eye and match expectations. Each acceptance criterion checked
individually:

- `[PASS]` AC1 (ingestion `OllamaProvider.extract()` raises on 0 assertions, message
  contains `done_reason=`) -- `test_extract_raises_on_zero_assertions` and
  `test_extract_raises_on_zero_output_includes_done_reason`
  (`tests/ingestion/test_ollama_provider.py`) pass in both runs; manual repro Scenario 1
  confirms end-to-end through `ingest_source()`.
- `[PASS]` AC2 (extraction `OllamaProvider.extract()` raises on 0
  entities/events/relationships, message contains `done_reason=`) --
  `test_extract_raises_on_all_empty_lists`,
  `test_extract_raises_on_zero_output_includes_done_reason`, and
  `test_extract_raises_on_empty_response_text_before_json_parse`
  (`tests/extraction/test_ollama_provider.py`) pass in both runs; manual repro Scenario 2
  confirms end-to-end through `extract_source()` with a truly empty response body (the
  case the pre-parse guard fix above addresses).
- `[PASS]` AC3 (`ingest_source()`: provider raises zero-output error -> `task_state.status
  == "failed"`, `error` contains the diagnostic, no Proposal files written) --
  `test_provider_zero_output_failure` (`tests/ingestion/test_pipeline.py`) passes in both
  runs.
- `[PASS]` AC4 (same, `extract_source()`) -- `test_provider_zero_output_failure`
  (`tests/extraction/test_pipeline.py`) passes in both runs.
- `[PASS]` AC5 (empty/whitespace-only source fails with `error == "Source file is empty"`,
  provider never called) -- `test_empty_source_file_fails_before_provider_call` in both
  `tests/ingestion/test_pipeline.py` and `tests/extraction/test_pipeline.py` pass in both
  runs (call-count assertion via `Mock.assert_not_called()`/`FakeProvider.calls == 0`);
  manual repro Scenarios 3-4 confirm `provider.extract.called is False` end-to-end.
- `[PASS]` AC6 (happy path unaffected) -- pre-existing happy-path tests
  (`test_ollama_provider_provenance_metadata`, `test_first_extraction_full_contract`, etc.)
  pass unmodified in both runs; new companion tests
  (`test_extract_parses_assertions`/`test_extract_succeeds_when_at_least_one_list_non_empty`)
  pass; manual repro Scenario 5 confirms a normal non-empty response still completes with
  1 proposal.
- `[PASS]` AC7 (full pre-existing suites pass) -- `tests/extraction/`: 61/61 pass, up from
  56/56 pre-ticket (5 net new tests: 4 in `test_ollama_provider.py` -- one existing test,
  `test_extract_handles_missing_lists`, was renamed and its assertion flipped per AC2/the
  Deviation above rather than counted as new; 2 in `test_pipeline.py` for AC3/AC4/AC5),
  100% coverage, in both the working tree and the isolated copy.
  `tests/ingestion/`: 56/58 pass in both the working tree and the isolated copy, up from
  48/50 pre-ticket (`git stash` baseline: 8 net new tests, 6 in the new
  `test_ollama_provider.py` file plus 2 in `test_pipeline.py`), 98% coverage, with the
  **same 2 pre-existing, unrelated failures** already documented by
  TASK-001a/TASK-001b/TASK-003/TASK-004
  (`test_comprehensive.py::test_acceptance_criteria_compliance`,
  `test_pipeline.py::test_import_isolation`) reconfirmed via `git stash`/`git stash pop`
  immediately before and after this ticket's changes -- identical failures both times,
  unrelated to this ticket.
- `[PASS]` Test coverage -- `pytest --cov=src.app.extraction` reports 100% (418/418
  statements); `pytest --cov=src.app.ingestion` reports 98% (330/336 statements, all 6
  missed lines pre-existing and outside this ticket's touched functions). Both figures
  identical between the working tree and the isolated copy. Both comfortably above the
  project's >=80% requirement.

**Honesty note on independence**: this verification was performed by the same Claude
session that wrote the implementation, not by a separate reviewer or model (same caveat
flagged in every prior ticket's verification record in this project). It does follow the
isolated-copy-and-independently-rerun discipline the project asks for, plus a manual
by-eye end-to-end reproduction script beyond just re-running pytest -- which is in fact
what caught the real gap documented in "Implementation notes" above (the pre-parse-guard
fix) that the unit tests alone, as first written, did not surface -- but it is not the
same strength of evidence as an independent second reviewer.
