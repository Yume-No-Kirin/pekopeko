# TASK-007: Backend API Layer for the Knowledge Core (V1)

- **Status**: completed

## Objective

Expose `src/app/ingestion` (`ingest_source`), `src/app/extraction` (`extract_source`),
`src/app/review` (`list_proposals`/`get_proposal`/`accept_proposal`/`reject_proposal`),
and `src/app/config` (`load_config`, read-only) over an HTTP/REST API, per ADI-010 —
lifting TASK-001/002/003/004's explicit "no GUI or CLI required" constraint for the first
time. Mandatory prerequisite for the entire GUI socle (`specs/tasks/BACKLOG-CLAUDE-V2.md`
section 1): none of TASK-008 through TASK-012 can be built without this connector.
Corresponds to the old `TASK-022` in `specs/tasks/BACKLOG-CLAUDE.md`.

New code only: a new `src/app/api/` package that imports and orchestrates the four
existing packages plus two small, additive, backward-compatible signature changes to
already-`completed` ingestion/extraction code (see Files/modules concerned). No change to
`review/` or `config/` — both are called exactly as already written.

## Binding context (references, not duplicated here)

- **ADI-010** (backend-api-layer, Accepted): protocol/framework (Flask), the async
  job/`task_id`-polling contract, `vault_root` via `PEKOPEKO_VAULT_ROOT` (API-only, never
  a request parameter), and the `PEKOPEKO_API_KEY` shared-secret security posture — this
  ticket implements ADI-010's decision, does not re-decide it.
- ADI-005 (sync-vs-async, Accepted): rule 1 (ingestion/extraction async), rule 3
  (accept/reject sync) — directly determines which endpoints are fire-and-poll vs
  request/response.
- ADI-008 (llm-provider-architecture, Accepted): the active provider is chosen by local
  config, never passed by the caller — this ticket's ingestion/extraction endpoints build
  their `Provider` via `build_configured_provider(load_config())`
  (`src/app/ingestion/providers/factory.py` / `src/app/extraction/providers/factory.py`,
  already existing, explicitly written "for callers of ingest_source(), never by
  pipeline.py itself"), never accept a provider choice over HTTP.
- `specs/domain/knowledge-invariants.md`:
  - INV-008/INV-009 (domain isolation / explicit cross-domain ops): `domain` is a
    required path parameter on every ingestion/extraction/review endpoint, validated at
    the HTTP boundary (see Domain validation below) in addition to each underlying
    module's own validation — never inferred, never allowed to leak another domain's
    data into a response scoped to one domain.
  - INV-011 (representations, including a GUI/API, are not the canonical knowledge
    model): this API must only project the existing canonical/proposal files — it
    creates no new persistence format of its own beyond the additive `task_id` field
    already covered by ADI-005/TKR-002.
- `specs/architecture/capabilities.md`: CAP-CORE-012 (Asynchronous Task Management,
  TKR-001/TKR-002) — governs the ingestion/extraction job contract; CAP-CORE-002/003/004
  (Human Validation, Provenance Tracking, Historical State Preservation) — same
  citations as TASK-002/005, now surfaced over HTTP rather than changed.
- `specs/product/use-cases.md`, UC-011 (Review Queue) — same V1 stage scope as
  TASK-002/005 (accumulation/listing, individual review, source inspection only); no
  bulk actions, no folder-path builder (both explicitly deferred to TASK-014/TASK-015 per
  `specs/tasks/BACKLOG-CLAUDE-V2.md`).

## Scope

New package `src/app/api/`:

1. **Ingestion endpoints** (async, per ADI-010 §2):
   - `POST /domains/<domain>/ingestions` — body `{"source_path": "<str>"}`. Validates
     `domain` against the fixed enum (see Domain validation) before doing anything else;
     mints `task_id = f"ingest-{uuid4()}"`; calls
     `create_task_state(source_path, domain, state_dir, task_id=task_id)` +
     `update_task_state(...)` **synchronously** (writes the `pending` state file before
     responding); starts a background thread running
     `ingest_source(vault_root, domain, Path(source_path), provider, state_dir,
     task_id=task_id)`; returns `202 {"task_id": ..., "status": "pending"}`.
   - `GET /domains/<domain>/ingestions/<task_id>` — `load_task_state(state_dir, task_id)`;
     `404` if not found, or if found but its `domain` field doesn't match the path
     `domain` (INV-008 boundary — never return another domain's task by id); else `200`
     with the `TaskState` fields as JSON.
   - `GET /domains/<domain>/ingestions` — optional `?status=` query filter; uses a new
     `list_task_states(state_dir) -> List[TaskState]` helper (see Files/modules
     concerned), then filters server-side by `domain` (and `status` if given) before
     returning the list as JSON.
2. **Extraction endpoints** — identical shape to Ingestion, under
   `/domains/<domain>/extractions`, calling `extract_source` / extraction's own
   `task_state.py` helpers.
3. **Review endpoints** (sync, per ADI-010 §3):
   - `GET /domains/<domain>/proposals` (optional `?status=`) → `list_proposals`.
   - `GET /domains/<domain>/proposals/<proposal_id>` → `get_proposal`.
   - `POST /domains/<domain>/proposals/<proposal_id>/accept` — body
     `{"reviewer_id": "<str>"}` → `accept_proposal`, `200` with the `AcceptResult` fields.
   - `POST /domains/<domain>/proposals/<proposal_id>/reject` — body
     `{"reviewer_id": "<str>", "reason": "<str, optional>"}` → `reject_proposal`, `200`
     with the `RejectResult` fields.
   - No edit endpoint: `review.edit_proposal` does not exist yet (TASK-006 not
     implemented) — out of scope here, matching `BACKLOG-CLAUDE-V2.md`'s TASK-007 scope
     ("review (accept/reject)" only; edit is TASK-013, once TASK-006 lands).
4. **Config endpoint** (sync, read-only, per ADI-010 §4):
   - `GET /config` → `load_config()`, all `PekopekoConfig` fields serialized as JSON
     (`Path` fields as strings). No write endpoint — out of scope (`BACKLOG-CLAUDE-V2.md`:
     "config (lecture)").
5. **Cross-cutting**, applied to every route above:
   - `X-API-Key` header checked against `PEKOPEKO_API_KEY` on every request; missing or
     wrong key → `401` before any handler logic runs (ADI-010 §5).
   - A manual CORS header (`Access-Control-Allow-Origin`) on every response so a
     React dev server on a different localhost port can call the API (no `flask-cors`
     dependency — a few lines in an `after_request` hook).
   - A single JSON error envelope for every non-2xx response:
     `{"error": {"type": "<ExceptionClassName>", "message": "<str>"}}`.
   - The Flask app binds to `127.0.0.1` only (ADI-010 §5) — never `0.0.0.0`.

### Domain validation

The fixed domain enum (`PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING`) is
re-declared once inside `src/app/api/` for early request-boundary validation
(`400` before any underlying call), deliberately duplicating the same literal each of
`ingestion/`, `extraction/`, and `review/` already keeps privately — matching this
project's established "no module imports another module's internals for shared
constants" convention (ROADMAP.md, TASK-002's "Indépendance entre modules" note), now
applied to the orchestration layer's own pre-check rather than skipping it and relying
solely on each module's internal (and inconsistently-raised — see Error mapping) domain
check.

### Error mapping (typed exception → HTTP status)

| Exception | Module | HTTP status |
|---|---|---|
| `ValueError` (bad domain) | `ingestion.pipeline` | 400 |
| `InvalidDomainError` | `extraction.errors`, `review.errors` | 400 |
| `ValidationError` | `extraction.errors`, `review.errors` | 400 |
| `ProposalNotFoundError` | `review.errors` | 404 |
| `SourceNotFoundError` | `review.errors` | 404 |
| `DomainMismatchError` | `review.errors` | 400 |
| `InvalidProposalStatusError` | `review.errors` | 409 |
| `UnsupportedProposalTypeError` | `review.errors` | 422 |
| `ConfigError` | `config.errors` | 500 |
| anything else unhandled | — | 500 |

`ingest_source`/`extract_source` swallow most internal failures into a
`status="failed"` result on the polled `TaskState` rather than raising — this table
only covers exceptions that can propagate synchronously out of an API handler (domain
pre-validation, review calls, config read).

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No bulk actions, no folder-path builder — same MVP boundary
  `specs/tasks/BACKLOG-CLAUDE-V2.md` sets for the whole GUI socle (TASK-014/015 add
  these later).
- No retrieval endpoint — old `BACKLOG-CLAUDE.md`'s TASK-022 mentioned retrieval, but the
  current authoritative backlog (`BACKLOG-CLAUDE-V2.md`, TASK-007 entry) scopes this
  ticket to ingestion/extraction/review/config only; retrieval gets its own backend
  ticket (TASK-018) and frontend ticket (TASK-019) later.
- No config *write* endpoint — `GET /config` only, matching "config (lecture)" literally.
  If TASK-008's Settings screen needs to edit config, that write endpoint is that
  ticket's own concern, not added here.
- No API versioning prefix (`/api/v1/...`) — single internal consumer (the React app
  from TASK-008 onward), not a public API; add one later only if a real second consumer
  appears.
- `reviewer_id` and `domain` remain explicit request fields, never inferred or derived
  from the API key — same posture as every prior ticket.

## Requirements

- Python only (ADI-007), Flask (ADI-010) — new dependency `flask>=3.0` in
  `src/requirements.txt`.
- No git usage (project-wide constraint).
- Directory creation, atomic writes, and all other on-disk behavior are entirely
  delegated to the four existing packages — the API layer does no file I/O of its own
  beyond what `list_task_states` needs (see below).
- The two pipeline signature changes below are additive only: calling
  `ingest_source`/`extract_source`/`create_task_state` without the new `task_id`
  argument must behave byte-for-byte as it does today (regression coverage required).

## Constraints

- No authentication beyond the single shared `X-API-Key` (no login, no per-user
  identity, no roles) — per ADI-010.
- No cross-domain operations — a request scoped to one `domain` never reads or lists
  another domain's data (INV-008/INV-009).
- No push/streaming channel for job progress (ADI-010) — polling only.
- No change to `review/`'s or `config/`'s public contracts — used exactly as TASK-002 and
  TASK-004 left them.
- Binds to `127.0.0.1` only — never exposed on a network interface.

## Files/modules concerned

- **New**: `src/app/api/app.py` — Flask app factory (`create_app() -> Flask`), route
  registration, `X-API-Key` check, CORS header, JSON error handler mapping the table
  above.
- **New**: `src/app/api/settings.py` — reads `PEKOPEKO_VAULT_ROOT` and `PEKOPEKO_API_KEY`
  from the environment at startup; raises immediately (process fails to start) if either
  is unset.
- **New**: `src/app/api/serialization.py` — JSON-dict helpers for `IngestionResult`,
  `ExtractionPipelineResult`, `TaskState`, `ProposalSummary`, `ProposalDetail`,
  `AcceptResult`, `RejectResult`, `PekopekoConfig` (dataclasses via `dataclasses.asdict`,
  `Path` fields to `str`).
- **New**: `src/app/api/tasks.py` — `run_in_background(fn, *args, **kwargs)` thin wrapper
  around `threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()`.
- **New**: `src/app/api/routes_ingestion.py`, `routes_extraction.py`, `routes_review.py`,
  `routes_config.py` — one Flask `Blueprint` per resource, per Scope above.
- **New**: `src/app/api/domains.py` — the re-declared fixed domain enum, used only for
  the API layer's own early `400` pre-check (see Domain validation).
- **Modified** (additive, backward-compatible): `src/app/ingestion/pipeline.py`
  (`ingest_source` gains `task_id: Optional[str] = None`, forwarded to
  `create_task_state`), `src/app/ingestion/task_state.py` (`create_task_state` gains
  `task_id: Optional[str] = None` — use it verbatim if given, else mint
  `f"ingest-{uuid4()}"` as today; new `list_task_states(state_dir: Path) ->
  List[TaskState]`, globbing `state_dir/*.json`, skipping files that fail to parse —
  same swallow behavior as `load_task_state`).
- **Modified**, mirrored: `src/app/extraction/pipeline.py` (`extract_source`) and
  `src/app/extraction/task_state.py` (`create_task_state`, new `list_task_states`) —
  identical shape to the ingestion changes above, kept as two separate edits per this
  project's module-independence convention (extraction never imports ingestion's code).
- **New tests**: `src/tests/api/` (route tests via Flask's `app.test_client()`), plus
  regression additions to `src/tests/ingestion/` and `src/tests/extraction/` covering the
  new optional `task_id` parameter and `list_task_states`.

## Dependencies

Depends on TASK-001, TASK-002, TASK-003, TASK-004 (all `completed`) through their public
function contracts only — no new dependency on TASK-005 or TASK-006 (both still
`backlog`; this ticket doesn't touch `review/`'s type restriction or add an edit
endpoint). Independent of TASK-005/TASK-006 — implementable in any order relative to
them.

## Acceptance criteria

1. `POST /domains/PERSONAL/ingestions` with a valid `source_path` returns `202` with a
   `task_id`; an immediate `GET` on that `task_id` never returns `404` (the pending state
   file already exists) and eventually reflects `status: "completed"` with
   `source_id`/`proposal_ids` populated, verified against a fake/stub `Provider` (no real
   Ollama calls).
2. `POST .../ingestions` with an invalid `domain` path segment returns `400` before any
   background thread starts, and no `TaskState` file is written.
3. `GET /domains/<domain>/ingestions` returns only tasks whose stored `TaskState.domain`
   matches the path `domain`, even when `state_dir` holds other-domain tasks.
4. `GET /domains/<domain>/ingestions/<task_id>` for a `task_id` belonging to a different
   domain returns `404`.
5. Criteria 1-4 hold identically for the extraction endpoints.
6. `GET /domains/<domain>/proposals` (no filter) returns the same proposals
   `review.list_proposals` would, JSON-serialized; `?status=PROPOSED` filters correctly.
7. `GET /domains/<domain>/proposals/<id>` for a missing id returns `404` with
   `error.type == "ProposalNotFoundError"`.
8. `POST .../accept` on a `PROPOSED` assertion proposal returns `200` with the
   `AcceptResult` fields, and the canonical assertion file exists on disk exactly as
   `review.accept_proposal` already guarantees (no reimplementation, pure pass-through).
9. `POST .../accept` on a non-`PROPOSED` proposal returns `409` with
   `error.type == "InvalidProposalStatusError"`.
10. `POST .../accept` on an entity/event/relationship proposal returns `422` with
    `error.type == "UnsupportedProposalTypeError"` (TASK-005 not yet landed).
11. `POST .../reject` with a `reason` returns `200`; the proposal file's
    `rejection_reason` is set accordingly.
12. `GET /config` returns `200` with `llm_provider.active`, `retrieval.index_dir` (as a
    string), `task_state.dir` (as a string), and `default.domain` present in the JSON
    body; no corresponding write endpoint exists.
13. A request with a missing or wrong `X-API-Key` header returns `401` for every route
    above, before any domain/business logic executes.
14. Starting the API without `PEKOPEKO_VAULT_ROOT` (or without `PEKOPEKO_API_KEY`) set
    fails at startup, before the server accepts any connection.
15. Every non-2xx JSON response follows `{"error": {"type": ..., "message": ...}}`, for
    at least one case per row of the Error mapping table.
16. Responses include a CORS header allowing a different localhost origin to read them
    (checked on at least one `GET` and one `POST`).
17. The app is configured to bind to `127.0.0.1` (inspected directly in
    `src/app/api/app.py`/its run entry point) — never `0.0.0.0`.
18. `ingest_source`/`extract_source` called without the new `task_id` argument (as
    TASK-001/003's existing tests already do) behave identically to before this ticket —
    all pre-existing `src/tests/ingestion/` and `src/tests/extraction/` tests pass
    unmodified.
19. `grep -r "git"` over `src/app/api/` shows no git usage.

## Testing requirements

`pytest`, Flask's `app.test_client()`, `tmp_path` for `vault_root`/`state_dir`, a
fake/stub `Provider` mirroring the pattern already used in `src/tests/ingestion/` and
`src/tests/extraction/` fixtures — no real Ollama calls, no real network calls. Minimum
cases: one test per acceptance criterion above (19 total), plus the existing
`src/tests/ingestion/` and `src/tests/extraction/` suites re-run unmodified as regression
coverage for Criterion 18.

## Out of scope

- Retrieval endpoints — TASK-018 (backend)/TASK-019 (frontend).
- Bulk operations, folder-path builder — TASK-014/TASK-015.
- `edit_proposal` endpoint — TASK-013, once TASK-006 lands.
- Config write endpoint (Settings screen backing) — a future ticket if TASK-008 needs it.
- Any actual React/frontend code — TASK-008 onward.
- API versioning, push/streaming job updates, multi-user auth — see ADI-010 Consequences.

## Implementation notes

- **`.env` loading in `settings.py`**: the ticket doesn't literally specify how
  `PEKOPEKO_VAULT_ROOT`/`PEKOPEKO_API_KEY` pick up a `.env` file, only that ADI-010
  describes "the same bounded, `.env`-loadable `PEKOPEKO_*` key convention TASK-004
  already established." `settings.py` calls `dotenv.load_dotenv()` (no explicit path —
  python-dotenv's default upward search from cwd) before reading the two env vars,
  independent of `config/loader.py`'s own `.env` loading (which is scoped to
  `~/.pekopeko/.env` specifically). A real process env var always wins (`override=False`).
- **Domain pre-check exception classes**: `api/domains.py` holds only the re-declared
  `VALID_DOMAINS` literal, exactly as the ticket's Files/modules concerned section
  describes. Each routes module's own early domain check raises the *same* exception
  class its underlying module would (`ValueError` in `routes_ingestion.py`,
  `extraction.errors.InvalidDomainError` in `routes_extraction.py`,
  `review.errors.InvalidDomainError` in `routes_review.py`) rather than a new
  API-specific class — this makes the ticket's Error mapping table rows for "bad domain"
  genuinely reachable and testable through the HTTP boundary (the API's own pre-check
  always fires first in practice, since its domain set is identical to each module's own,
  making the module-internal check effectively unreachable defense-in-depth — consistent
  with the ticket's "in addition to each underlying module's own validation" wording).
- **Non-atomic `TaskState.save()` race, found during verification**: `TaskState.save()`
  (pre-existing TASK-001/003 code, unmodified by this ticket beyond the additive
  `task_id`/`list_task_states` changes) opens the same filename for write on every
  status update, without an atomic temp-file-then-rename swap (unlike
  `review/storage.py`'s `_write_atomic_file`). Reproduced independently
  (`/tmp/repro.py`, 30 iterations, instrumented to check both the raw filesystem and the
  HTTP response): an immediate `GET .../<task_id>` right after the `202` can race the
  background job's own near-simultaneous first status-update write, observe a
  transiently truncated file, and have `load_task_state` swallow the resulting
  `JSONDecodeError` into `None` — indistinguishable from a genuinely unknown task_id,
  producing a spurious `404` and violating AC1's "an immediate GET on that task_id never
  returns 404." Fixed at the API layer only (no change to `ingestion`/`extraction`'s
  `task_state.py` writer): a new `load_task_state_resilient()` helper in
  `src/app/api/tasks.py`, used by `routes_ingestion.get_ingestion` and
  `routes_extraction.get_extraction`, retries briefly (up to 25 attempts, 10ms apart)
  only while the state file exists on disk but hasn't parsed yet, and returns `None`
  immediately (no retry) when the file never existed at all — so AC2/AC4's genuinely-404
  cases stay fast. Covered by a deterministic unit test (`src/tests/api/test_tasks.py`,
  no timing dependency) plus reran the original race reproduction 5x after the fix with
  zero failures (down from a reliable repro before it).

## Verification record (2026-09-01)

Implemented by Claude (this session): new `src/app/api/` package (10 files) plus two
mirrored additive edits to already-`completed` code (`src/app/ingestion/{pipeline.py,
task_state.py}`, `src/app/extraction/{pipeline.py,task_state.py}` — new optional
`task_id` parameter, new `list_task_states`), `flask>=3.0` added to
`src/requirements.txt`, new `src/tests/api/` (66 tests), plus regression tests added to
`src/tests/ingestion/` and `src/tests/extraction/` for the new `task_id` parameter and
`list_task_states`. Four pre-existing guard tests from TASK-001b/TASK-004
(`test_ingest_source_signature_unchanged`/`test_extract_source_signature_unchanged` in
`test_pipeline.py`, `test_ingest_source_signature_is_unchanged`/
`test_extract_source_signature_is_unchanged` in `test_provider_factory.py`) were updated
to expect the new sanctioned `task_id` parameter rather than the old fixed signature.

Per this project's verification discipline: code was copied to an isolated scratch
directory outside the repo three separate times across the session
(`/tmp/pekopeko_verify{,2,3}/`) as the implementation was fixed, and the full
`src/tests/{ingestion,extraction,review,config,api}/` suites re-run independently there
each time, rather than trusting the in-repo run alone. The last isolated copy
(`/tmp/pekopeko_verify3/`) was run to completion after all fixes and is the baseline for
the numbers below; `src/tests/api/` alone was additionally re-run 5x in a row there (and
3x in the working tree) to rule out the race described above as flakiness rather than a
fixed bug. Each acceptance criterion checked individually:

- `[PASS]` AC1 (`POST /domains/PERSONAL/ingestions` → `202` + `task_id`; immediate `GET`
  never `404`; eventually `completed` with `source_id`/`proposal_ids`, fake provider, no
  real Ollama calls) — `test_start_ingestion_returns_202_and_eventually_completes`
  passes; the immediate-`GET`-never-404 half was the one that initially reproduced the
  non-atomic-write race above (see Implementation notes) — now passes reliably after the
  `load_task_state_resilient` fix, confirmed via both the pytest suite and a standalone
  30-iteration instrumented repro script with zero failures.
- `[PASS]` AC2 (invalid domain on `POST` → `400` before any thread starts, no
  `TaskState` file written) —
  `test_start_ingestion_invalid_domain_returns_400_before_any_write` passes, asserting
  the `ingestion` state subdirectory has no `*.json` files afterward.
- `[PASS]` AC3 (`GET` list scoped to path `domain`, even with other-domain tasks
  present) — `test_list_ingestions_scoped_to_domain` passes (creates a `PERSONAL` and a
  `FICTION` task, confirms the `FICTION` one is absent from the `PERSONAL` listing).
- `[PASS]` AC4 (`GET .../<task_id>` for a task belonging to a different domain →
  `404`) — `test_get_ingestion_wrong_domain_returns_404` passes.
- `[PASS]` AC5 (criteria 1-4 hold identically for extraction) —
  `test_start_extraction_returns_202_and_eventually_completes`,
  `test_start_extraction_invalid_domain_returns_400_before_any_write`,
  `test_list_extractions_scoped_to_domain`, `test_get_extraction_wrong_domain_returns_404`
  all pass, mirroring the ingestion tests.
- `[PASS]` AC6 (`GET /domains/<domain>/proposals` matches
  `review.list_proposals`, JSON-serialized; `?status=` filters) —
  `test_list_proposals_matches_and_filters_by_status` passes.
- `[PASS]` AC7 (`GET .../proposals/<id>` for a missing id → `404`,
  `error.type == "ProposalNotFoundError"`) — `test_get_proposal_missing_returns_404`
  passes.
- `[PASS]` AC8 (`POST .../accept` on a `PROPOSED` assertion → `200` with `AcceptResult`
  fields, canonical assertion file exists exactly as `review.accept_proposal`
  guarantees) — `test_accept_proposed_assertion_returns_200_and_writes_canonical_file`
  passes, asserting `Path(response["assertion_path"]).exists()`.
- `[PASS]` AC9 (`POST .../accept` on non-`PROPOSED` → `409`,
  `error.type == "InvalidProposalStatusError"`) — `test_accept_non_proposed_returns_409`
  passes.
- `[PASS]` AC10 (`POST .../accept` on entity/event/relationship → `422`,
  `error.type == "UnsupportedProposalTypeError"`) —
  `test_accept_entity_proposal_returns_422` passes.
- `[PASS]` AC11 (`POST .../reject` with `reason` → `200`, `rejection_reason` set on
  disk) — `test_reject_with_reason_returns_200_and_sets_rejection_reason` passes,
  asserting the reason string appears in the live proposal file's own bytes.
- `[PASS]` AC12 (`GET /config` → `200` with `llm_provider.active`,
  `retrieval.index_dir`/`task_state.dir` as strings, `default.domain` present; no write
  endpoint) — `test_get_config_returns_required_fields` and
  `test_no_config_write_endpoint` pass.
- `[PASS]` AC13 (missing/wrong `X-API-Key` → `401` for every route, before any
  domain/business logic — including when the domain in the URL is itself invalid) —
  `test_auth.py` parametrizes over 10 representative routes (all four resource groups,
  GET and POST) for both missing and wrong keys (20 cases), plus
  `test_missing_api_key_on_invalid_domain_still_401_not_400` confirming the 401 wins
  over what would otherwise be a 400.
- `[PASS]` AC14 (missing `PEKOPEKO_VAULT_ROOT`/`PEKOPEKO_API_KEY` fails at startup,
  before accepting any connection) — `test_startup.py`'s
  `test_missing_vault_root_raises_at_startup`/`test_missing_api_key_raises_at_startup`
  pass (`MissingSettingError` raised by `load_settings()`, called synchronously inside
  `create_app()` before the Flask app object is even returned); also manually confirmed
  by starting the real dev server (`python -m src.app.api.app`) with a real HTTP smoke
  test afterward (see below) — the process only accepted connections once both variables
  were set.
- `[PASS]` AC15 (every non-2xx response follows the JSON error envelope, at least one
  case per Error mapping table row) — `test_error_mapping.py` covers all 9 distinct
  status/exception rows: `ValueError`→400, both `InvalidDomainError`
  variants→400 (via `routes_extraction`/`routes_review`), both `ValidationError`
  variants→400 (via a throwaway diagnostic route added to the `app` fixture, since
  `ingest_source`/`extract_source` swallow these internally rather than ever raising
  them synchronously — see the module's own docstring), `ProposalNotFoundError`→404,
  `DomainMismatchError`→400, `InvalidProposalStatusError`→409,
  `UnsupportedProposalTypeError`→422, `ConfigError`→500 (same throwaway-route
  technique), plus an unregistered `RuntimeError`→500 fallback case. A structural test
  (`test_error_status_map_covers_every_ticket_row`) additionally asserts the
  `ERROR_STATUS_MAP` dict itself has the correct status for every row by class name.
- `[PASS]` AC16 (CORS header present on at least one `GET` and one `POST`) —
  `test_cors.py`'s two tests pass; also confirmed via the real dev-server smoke test
  (`curl -D -` showing `Access-Control-Allow-Origin: *` on a live `GET /config`).
- `[PASS]` AC17 (app binds `127.0.0.1` only, never `0.0.0.0`, inspected directly in
  `app.py`) — `test_run_entry_point_binds_localhost_only` passes (source-text
  inspection, per the ticket's own wording); also directly observed on the real
  dev-server run (`* Running on http://127.0.0.1:5000`).
- `[PASS]` AC18 (`ingest_source`/`extract_source` called without `task_id` behave
  identically to before) — the full pre-existing `src/tests/ingestion/` (48/50 passing,
  2 documented pre-existing failures unrelated to this ticket — same
  `test_acceptance_criteria_compliance`/`test_import_isolation` failures already noted
  against TASK-001a/001b/004, reproduced independently before touching any code to
  confirm they predate this ticket) and `src/tests/extraction/` (56/56 passing) suites
  re-run unmodified (beyond the four signature-guard-test updates noted above, which
  assert the new sanctioned signature rather than change pipeline behavior).
- `[PASS]` AC19 (no git usage in `src/app/api/`) —
  `test_no_git_usage_in_api_package` passes; also independently confirmed via
  `grep -ril "git" src/app/api/*.py` (no matches) outside of pytest.
- `[PASS]` Test coverage — `pytest --cov=src/app/api` reports 99% line coverage
  (247/250 statements; the 3 uncovered lines are the `main()`/`__main__` process entry
  point, not meaningfully unit-testable without starting a real server) — well above the
  project's 80% minimum. `src/tests/api/` totals 66 tests, all passing, reproduced 5x in
  a row with zero flakes after the race fix above.
- `[PASS]` Real end-to-end smoke test (beyond the pytest suite): started the actual
  Flask dev server (`PEKOPEKO_VAULT_ROOT`/`PEKOPEKO_API_KEY`/`PEKOPEKO_TASK_STATE_DIR`
  pointed at a scratch directory), confirmed `401` with no key and `200` with the
  correct key on `GET /config` over real HTTP, `202` + `task_id` on a real
  `POST /domains/PERSONAL/ingestions` against a deliberately-missing source file, and
  inspected the resulting on-disk `TaskState` JSON: `status: "failed"` with a readable
  `error` message and a populated `events` log — confirming ADI-005 rule 1 (a failed
  async job never surfaces as an HTTP error on the original `POST`, only via the polled
  `TaskState`) holds against the real Flask WSGI server, not just `app.test_client()`.

Same limitation as every prior ticket in this project: verification was performed by the
same Claude session that wrote the implementation, not by a second independent
reviewer.
