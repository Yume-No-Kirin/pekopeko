# TASK-001a: Enriched Extraction Provenance Metadata (V1)

- **Status**: completed

## Objective

Extend TASK-001's ingestion pipeline (`completed`) so the `provenance` dict already
written on every Assertion Proposal carries the LLM extraction details that
`specs/ux-design/pekopeko-proposal-detail.html`'s "Provenance & Extraction" section shows
(model, temperature, extraction ID, extraction duration) but that TASK-001's frontmatter
contract never captured. Satellite ticket to TASK-001, not an amendment to its file: keeps
TASK-001's own historical record and already-cited acceptance criteria numbering stable,
per this project's "additive satellite ticket, letter-suffixed off the ticket it extends"
convention (same posture as TASK-004's/TASK-007's own additive amendments to completed
work). Exists so that TASK-011 (Proposal Detail screen) can render the mockup's Provenance
section in full instead of silently dropping fields the mockup shows but the backend never
recorded.

## Binding context (references, not duplicated here)

- `specs/tasks/completed/TASK-001-data-ingestion.md`: current required Proposal
  `provenance` dict is "minimum `source_id` ... and `extraction_provider`" — this ticket
  adds to that minimum, doesn't replace it.
- ADI-008 (llm-provider-architecture, Accepted): pipeline code depends only on the
  `Provider` protocol (`extract(text, context) -> ExtractionResult`), never a concrete SDK
  — the new metadata must flow through that same interface, not a provider-specific
  backdoor.
- `specs/domain/knowledge-invariants.md` INV-002/INV-016: provenance to the exact source
  and processing step — this ticket strengthens that traceability, doesn't introduce a new
  invariant.
- `specs/ux-design/pekopeko-proposal-detail.html`, "Provenance & Extraction" section:
  Provider LLM, Modèle, Température, Extraction ID, Durée extraction — the concrete target
  shape this ticket exists to make renderable.
- `specs/tasks/backlog/TASK-011-proposal-detail-screen.md`: depends on this ticket for its
  Provenance section's full fidelity to the mockup.

## Scope

1. Extend the `Provider` protocol's return shape (`ExtractionResult`, in
   `ingestion/providers/base.py`) with optional metadata a concrete provider may supply:
   `model: Optional[str]`, `temperature: Optional[float]`. Optional because a future,
   simpler `Provider` implementation (e.g. a rule-based or test provider) may have no
   meaningful model/temperature to report.
2. `ingestion/providers/ollama_provider.py`'s `OllamaProvider` populates both fields from
   its own already-configured `model`/settings (no new user-facing config surface — these
   values already exist on the provider instance via `providers/factory.py`, just weren't
   surfaced into the result before).
3. `ingestion/pipeline.py`'s `ingest_source` measures wall-clock duration around the
   `provider.extract(...)` call and mints a fresh `extraction_id` (`extract-<uuid4>`, minted
   by the pipeline, not the provider — mirrors how `source_id`/`proposal_id` are already
   pipeline-minted, never provider-supplied).
4. `ingestion/storage.py`'s Proposal-writing helper adds four keys to the `provenance` dict
   already written for every Proposal: `provider_model`, `provider_temperature`,
   `extraction_id`, `extraction_duration_seconds`. All four `null` when the concrete
   `Provider` doesn't supply `model`/`temperature` (duration/`extraction_id` are always
   present — pipeline-computed, provider-independent).

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Purely additive: no change to `provenance`'s existing required keys (`source_id`,
  `extraction_provider`), no change to `ingest_source`'s public signature.
- `model`/`temperature` are optional on the `Provider` protocol — a provider that doesn't
  report them yields `null` on the Proposal, never a fabricated/guessed value, never an
  exception.
- `extraction_duration_seconds` measures only the `provider.extract(...)` call itself, not
  the full `ingest_source` pipeline (file read, dedup check, source write) — matches what
  "Durée extraction" in the mockup is actually describing (LLM call time, distinct from
  total ingestion time already visible via `TaskState.started_at`/`completed_at`).
- `extraction_id` is one per `ingest_source` call (one extraction call currently produces
  N assertions in one provider round-trip, per TASK-001's scope) — not one per assertion.
  All N Proposals from the same ingestion share the same `extraction_id`.

## Requirements

- Python only (ADI-007). No new dependency.
- No change to any file outside `ingestion/` (`extraction/`, `review/`, `config/`,
  `api/` untouched by this ticket).
- No git usage (project-wide constraint).

## Constraints

- No change to `ingest_source`'s public parameter list.
- No new required frontmatter field — all four additions are optional/nullable.
- No retroactive backfill of already-written Proposal files — this ticket only changes
  what new ingestions write going forward.
- No consumption of these fields anywhere in `ingestion/` itself beyond writing them (no
  new validation/business logic keyed on `provider_model`, etc.) — purely data capture for
  downstream consumers (TASK-011).

## Files/modules concerned

- `ingestion/providers/base.py` — `ExtractionResult` gains optional `model`/`temperature`.
- `ingestion/providers/ollama_provider.py` — populates both from the provider's own config.
- `ingestion/pipeline.py` — measures extraction duration, mints `extraction_id`.
- `ingestion/storage.py` — Proposal `provenance` dict gains the four new keys.
- `tests/ingestion/` — new/updated tests for the four new fields (present + correct for
  `OllamaProvider`; `null` for a fake `Provider` that doesn't supply
  `model`/`temperature`), regression coverage confirming existing TASK-001 tests still
  pass unmodified.

## Dependencies

Depends on TASK-001 (`completed`) as the ticket it extends. No dependency on TASK-003,
TASK-005, TASK-006, or TASK-007 — purely internal to `ingestion/`.

## Acceptance criteria

1. Ingesting a source with `OllamaProvider` produces Proposals whose `provenance` dict
   includes non-null `provider_model` (matching the provider's configured model) and
   `provider_temperature` (matching its configured temperature).
2. Every Proposal from the same `ingest_source` call shares the same `extraction_id`; two
   separate `ingest_source` calls produce two different `extraction_id` values.
3. `extraction_duration_seconds` is present, numeric, and greater than 0 on every Proposal
   written by a successful ingestion.
4. Using a fake/minimal test `Provider` whose `ExtractionResult` doesn't set
   `model`/`temperature` yields `provider_model: null`/`provider_temperature: null` on the
   resulting Proposals — no exception, no fabricated default.
5. All pre-existing `tests/ingestion/` tests pass unmodified (same 29/31 baseline as
   TASK-001/TASK-004's verification records — the 2 pre-existing unrelated failures stay
   unrelated and unaffected).
6. `ingest_source`'s public parameter list is unchanged from TASK-001/TASK-004 (verified
   via `inspect.signature`, same pattern already used in TASK-004's tests).

## Testing requirements

`pytest`, `tmp_path`, no real network calls (stub/fake `Provider` for the metadata-absent
case, existing test-double pattern for `OllamaProvider` construction). Minimum: one test
per acceptance criterion above. Coverage discipline (≥80%) applies to the touched portions
of `ingestion/`.

## Out of scope

- Retroactive backfill of `provenance` on already-written Proposal files.
- A second concrete provider reporting these fields — only `OllamaProvider` is touched
  here (TASK-020, a future second provider, inherits this contract when it lands).
- Any GUI — TASK-011 consumes this ticket's output, implemented separately.
- Extending `extraction/` (TASK-003's entity/event/relationship pipeline) with the same
  metadata — out of scope here since TASK-010/011 are assertion-only; a symmetric ticket
  for `extraction/` can be proposed later if TASK-012 (entity/event/relationship GUI)
  needs it.

## Deviation from this ticket, flagged and resolved with Cleo before implementation (2026-08-31)

This ticket's scope item 2 assumed `OllamaProvider` already had a configured `temperature`
that "just wasn't surfaced" into the result. False: `temperature` did not exist anywhere in
the codebase before this implementation — not in `OllamaProviderConfig`, not in
`config/schema.py`, never sent to Ollama's `/api/generate` call. Resolution, confirmed with
Cleo: added a real `temperature: float = 0.7` field to `OllamaProviderConfig` (the
provider's own dataclass, not the shared `config/schema.py` — preserves "no new
user-facing config surface"), and actually wired it into the Ollama API call via
`options.temperature`, so `provider_temperature` reports a value that genuinely affects
generation rather than being a cosmetic echo. `model` needed no such fix — it already
existed on `OllamaProviderConfig`/`providers/factory.py` exactly as the ticket assumed.

## Implementation notes

- `ingestion/providers/base.py`: `ExtractionResult` gained `model: Optional[str] = None`
  and `temperature: Optional[float] = None`.
- `ingestion/providers/ollama_provider.py`: `OllamaProviderConfig` gained
  `temperature: float = 0.7` (see Deviation above); `extract()`'s request payload gained
  `"options": {"temperature": self.config.temperature}`; `extract()` now returns
  `ExtractionResult(assertions=..., model=self.config.model, temperature=self.config.temperature)`.
- `ingestion/pipeline.py`'s `ingest_source`: mints `extraction_id = f"extract-{uuid.uuid4()}"`
  once per call, before the `provider.extract(...)` call; measures
  `extraction_duration_seconds` with `time.monotonic()` bracketing only that call (not file
  read/dedup/source write); both, plus `extraction_result.model`/`.temperature`, are passed
  to `write_proposal_file(...)` for every assertion from that call, so all Proposals from one
  `ingest_source` call share one `extraction_id`.
- `ingestion/storage.py`'s `write_proposal_file` gained four new optional (default `None`)
  parameters, appended after the existing ones so no existing caller broke: `provider_model`,
  `provider_temperature`, `extraction_id`, `extraction_duration_seconds` — all four written
  into the `provenance` dict. Existing required keys (`source_id`, `extraction_provider`) and
  `_validate_frontmatter`'s required-fields list are untouched.
- Five new tests added to `tests/ingestion/test_pipeline.py`, one per AC1-4/AC6 (AC5 is the
  unchanged-suite check itself, not a new test).

## Verification record (2026-08-31)

Implemented by Claude (this session). Per this project's verification discipline: code
(`src/app/ingestion/`, `src/tests/ingestion/`) was copied to an isolated scratch directory
outside the repo (`.../scratchpad/task001a_verify/`) and the test suite re-run independently
there, rather than trusting the in-repo run alone. A hand-written manual reproduction script
ran a real `OllamaProvider.extract()` call (with `requests.post` stubbed, no real network
call) through `ingest_source()` end-to-end and printed the written Proposal file's full
`provenance` dict plus the exact JSON payload sent to Ollama's API, for by-eye inspection.
Each acceptance criterion checked individually:

- `[PASS]` AC1 (non-null `provider_model`/`provider_temperature` from `OllamaProvider`,
  matching its config) -- `test_ollama_provider_provenance_metadata` passes in both the
  working tree and the isolated copy; the manual reproduction script's printed
  `provenance` dict showed `provider_model: llama3`, `provider_temperature: 0.55` matching
  the constructed config, and the printed Ollama request payload showed
  `{'temperature': 0.55}` was actually sent -- not a cosmetic echo.
- `[PASS]` AC2 (all Proposals from one `ingest_source` call share one `extraction_id`; two
  calls produce two different ids) -- `test_extraction_id_shared_within_call_differs_across_calls`
  passes in both runs.
- `[PASS]` AC3 (`extraction_duration_seconds` present, numeric, `> 0`) --
  `test_extraction_duration_recorded` (uses a provider stub with an artificial `time.sleep`
  to guarantee a measurable, non-flaky duration) passes in both runs.
- `[PASS]` AC4 (a fake `Provider` that leaves `model`/`temperature` at their `None` defaults
  yields `provider_model: null`/`provider_temperature: null`, no exception) --
  `test_fake_provider_yields_null_model_temperature` passes in both runs.
- `[PASS]` AC5 (all pre-existing `tests/ingestion/` tests pass unmodified, same 29/31
  baseline) -- confirmed by running the full suite before this ticket's changes
  (`git stash`) and after (`git stash pop`): identical 2 pre-existing failures both times
  (see below), 29 passing both times pre-change; 34 passing post-change (29 + 5 new).
  Isolated-copy run matches exactly.
- `[PASS]` AC6 (`ingest_source`'s public parameter list unchanged) --
  `test_ingest_source_signature_unchanged` (`inspect.signature`, same pattern as TASK-004's
  tests) passes in both runs.
- `[PASS]` Test coverage on touched files -- working tree and isolated copy report identical
  figures: `providers/base.py` 100%, `storage.py` 96%, `providers/ollama_provider.py` 86%,
  `pipeline.py` 83% (overall `app/ingestion` 88%). All comfortably above the project's >=80%
  requirement.
- `[PASS]` 34/36 `tests/ingestion/` pass in the working tree and again, independently, in the
  isolated scratch copy -- identical figures both places.

**Pre-existing failures, confirmed unrelated to this ticket** (same two as documented in
TASK-004's verification record, re-confirmed here via `git stash`/`git stash pop` before and
after this ticket's changes): `test_comprehensive.py::test_acceptance_criteria_compliance`
and `test_pipeline.py::test_import_isolation`, both failing on a hardcoded
`Path("app/ingestion/pipeline.py")` relative-path read that doesn't match this repo's actual
run-from-root convention, regardless of this ticket. Left untouched per this ticket's scope
(no unrelated cleanup).

**Honesty note on independence**: this verification was performed by the same Claude session
that wrote the implementation, not by a separate reviewer or model (same caveat as TASK-002/
003/004's verification records). It does follow the isolated-copy-and-independently-rerun
discipline the project asks for, plus a manual by-eye reproduction script beyond just
re-running pytest, but it is not the same strength of evidence as an independent second
reviewer.
