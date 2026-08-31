# TASK-007: Backend API Layer for the Knowledge Core (V1)

- **Status**: backlog

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
  bulk actions, no folder-path builder (both explicitly deferred to TASK-013/TASK-015 per
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
     ("review (accept/reject)" only; edit is TASK-014, once TASK-006 lands).
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
  `specs/tasks/BACKLOG-CLAUDE-V2.md` sets for the whole GUI socle (TASK-013/015 add
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
- Bulk operations, folder-path builder — TASK-013/TASK-015.
- `edit_proposal` endpoint — TASK-014, once TASK-006 lands.
- Config write endpoint (Settings screen backing) — a future ticket if TASK-008 needs it.
- Any actual React/frontend code — TASK-008 onward.
- API versioning, push/streaming job updates, multi-user auth — see ADI-010 Consequences.
