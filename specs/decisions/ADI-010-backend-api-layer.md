# ADI-010: Backend API Layer and Frontend Integration Contract

- **ID**: ADI-010
- **Date**: 2026-08-31
- **Status**: Accepted (confirmed by Cleo on 2026-08-31)

## Context

ADI-009 chose ReactJS for the frontend but explicitly scoped itself out of "how the
interface talks to the backend," deferring that question to "a future ticket once that
work is actually scoped." `specs/tasks/BACKLOG-CLAUDE-V2.md` (TASK-007, "Couche API
backend pour le Knowledge Core") now makes that ticket concrete: TASK-001 (ingestion),
TASK-002 (review), TASK-003 (extraction), and TASK-004 (config) only expose pure Python
functions, each explicitly scoped "no GUI or CLI required." TASK-008 through TASK-012
(the GUI socle) cannot be built without a connector — writing that connector ticket
surfaces four genuine architectural gaps with no existing answer in the corpus:

1. **Protocol/framework** — no HTTP/web framework exists anywhere in
   `src/requirements.txt` today.
2. **Async job shape** — ADI-005 already decided ingestion/extraction must be
   asynchronous from the user's perspective and review accept/reject synchronous, but
   never decided how an HTTP client observes an asynchronous job's progress (poll vs
   push, what identifies a job).
3. **`vault_root` placement** — `docs/ROADMAP.md` (TASK-004 amendment note) confirms
   `vault_root` has no config surface anywhere: it is a required explicit parameter on
   every `ingest_source`/`extract_source`/review function call today, supplied by
   whichever Python caller invokes them directly. An HTTP API sitting behind those
   functions needs to obtain it from somewhere without turning it into a
   client-supplied, arbitrary-filesystem-path request parameter.
4. **Security posture** — none of TASK-001 through TASK-006 implement or require
   authentication (`reviewer_id`/`domain` are "trusted as given"); an HTTP server is the
   first component in this codebase reachable by something other than a direct Python
   call, which changes the trust boundary.

Per AGENTS.md, "a significant architecture decision belongs in `specs/decisions/` as a
real ADR file" — and per this project's own precedent, ADI-007/008/009 were each written
"en butant sur des gaps bloquants pour écrire un ticket implémentable" (ROADMAP.md). This
ADR resolves those four gaps so that TASK-007 (and every later GUI-facing ticket that
adds an endpoint) has a fixed contract to implement against, rather than each ticket
re-deciding protocol/framework/security ad hoc.

## Decision

**HTTP/REST over Flask**, added as the sole new backend dependency (`flask>=3.0`), used
exactly the way ADI-005 already governs sync vs async at the *operation* level:

1. **Protocol and framework.** Plain synchronous Flask (WSGI, not ASGI). No function in
   `ingestion/`, `extraction/`, `review/`, or `config/` is `asyncio`-native today — Flask
   matches that blocking style with zero new runtime paradigm. FastAPI's async-native
   model and automatic OpenAPI generation were considered and rejected as unneeded
   complexity for a single local consumer (see Alternatives).

2. **Async job contract (ingestion/extraction).** A `POST` that starts an ingestion or
   extraction job:
   - runs the existing blocking `ingest_source`/`extract_source` call on a background
     thread (Python `threading.Thread`, daemon), never blocking the HTTP response;
   - returns `202 Accepted` immediately with a `task_id` string;
   - the `task_id` is minted and its `TaskState` file written to disk **synchronously,
     before** the HTTP response is sent and **before** the background thread starts —
     eliminating the race where a client polls before any state file exists. This
     requires `ingest_source`/`extract_source` (and their `create_task_state` helpers) to
     accept an already-minted `task_id` as a new, optional, backward-compatible
     parameter (default `None` preserves today's behavior — TASK-001/003's existing
     tests and callers are unaffected).
   - a client observes progress by polling `GET .../<task_id>` (reads the same
     `TaskState` JSON file already written by TASK-001/003's task-state mechanism per
     ADI-005/TKR-002) — no push/websocket channel in V1.
   - a job that fails after being accepted never surfaces as an HTTP error status on the
     original `POST`; the failure is only visible via the polled
     `TaskState.status == "failed"` — matching ADI-005 rule 1 (the user is never blocked
     on AI/LLM processing, including on its failure).

3. **Synchronous operations (review, config).** `GET`/`POST` endpoints over
   `review.list_proposals/get_proposal/accept_proposal/reject_proposal` and
   `config.load_config` call straight through and return a normal `200` (or a
   `4xx`/`5xx` mapped from the underlying typed exception) in the same request — per
   ADI-005 rule 3, exactly as those functions already behave when called directly.

4. **`vault_root` source.** A new environment variable, `PEKOPEKO_VAULT_ROOT`, read once
   by the API process at startup and used for every request; the API process fails fast
   at startup if it is unset. It is **never** accepted as an HTTP request parameter (a
   client-supplied filesystem path would be a path-traversal / arbitrary-file-access
   surface, and this is a single-vault-per-device tool — no request ever legitimately
   needs a different one). This does **not** extend `src/app/config/`'s `PekopekoConfig`
   schema — `vault_root` stays local to the new `api/` package's own startup, consistent
   with TASK-004's deliberate choice to give `vault_root` no config surface at all, and
   with TASK-007's own backlog scope ("config (lecture)" = read the existing config, not
   grow its schema).

5. **Security posture.** The API binds to `127.0.0.1` only (never `0.0.0.0`), and every
   request (except a liveness/health check, if one is added) must carry a shared secret
   via an `X-API-Key` header, checked against a new `PEKOPEKO_API_KEY` environment
   variable — the same bounded, `.env`-loadable `PEKOPEKO_*` key convention TASK-004
   already established (`python-dotenv`, already a pinned dependency). A request with a
   missing or wrong key gets `401 Unauthorized` before any domain/business logic runs.
   This is defense against another local process on the same machine calling the API by
   accident or design, not a multi-tenant auth system — there is still exactly one
   implicit user/reviewer, `reviewer_id` stays an explicit, trusted-as-given request
   field exactly as in TASK-002/005/006, and no login/session/user-identity concept is
   introduced.

Every future ticket that adds an HTTP endpoint (retrieval search TASK-019, bulk
operations TASK-015, a future config-write endpoint for Settings, etc.) extends this same
contract — REST + Flask, the same async-job-via-`task_id`-polling shape for any future
asynchronous operation, the same `X-API-Key` check, the same `127.0.0.1`-only bind —
rather than re-deciding it per ticket.

## Alternatives considered

- **FastAPI.** Rejected for V1: its value (Pydantic request/response validation,
  automatic OpenAPI docs, native `asyncio`) doesn't match a codebase where every existing
  function is a blocking, synchronous Python call — adopting it would mean either
  wrapping every call in a thread pool executor anyway (no different from Flask's default
  threaded dev server) or a much larger rewrite to make the Knowledge Core itself
  `asyncio`-native, which nothing in ADI-005 through ADI-008 asks for. Revisit only if a
  real need for native async I/O emerges later.
- **A WebSocket or Server-Sent-Events push channel for job progress**, instead of
  polling. Rejected for V1: adds a persistent-connection dependency and client-side
  complexity (reconnect/backoff logic) the mockups in `specs/ux-design/` don't call for
  (the Ingestion Logs screen is a periodically-refreshed table, not a live stream) —
  polling `GET .../<task_id>` is simpler and still satisfies ADI-005's "resumable...
  task state" framing (a client can always re-poll after a page reload with no lost
  context).
- **Extending `PekopekoConfig` with a `vault_root` field**, instead of an API-only env
  var. Rejected: `vault_root` was a deliberate omission from TASK-004's schema (per
  `docs/ROADMAP.md`'s amendment note), and growing that shared schema is out of
  TASK-007's stated scope ("config (lecture)"). Keeping it local to `api/` avoids
  re-opening a settled TASK-004 decision for a need specific to the new API process.
- **No authentication at all** (bind to `127.0.0.1` only, trust every local process).
  Considered and rejected in favor of the lightweight shared-token option above — an
  explicit choice made when presented with both, favoring defense against another local
  process/tool touching the vault's proposal-review or ingestion pipeline unintentionally.
- **Per-request `vault_root`/API-key query parameters** instead of headers/env vars.
  Rejected as sloppier HTTP convention (secrets/paths belong in headers or process
  config, not URLs that get logged) with no offsetting benefit.

## Consequences

- `src/requirements.txt` gains `flask>=3.0`. No other new runtime dependency (CORS
  handled with a manual `after_request` header, no `flask-cors`; the token check is a
  few lines, no auth library).
- `ingest_source`/`extract_source` (`src/app/ingestion/pipeline.py`,
  `src/app/extraction/pipeline.py`) and their `create_task_state` helpers
  (`task_state.py` in both packages) gain a new optional `task_id: Optional[str] = None`
  parameter — an additive, backward-compatible change to two already-`completed`
  tickets (TASK-001/TASK-003), the same category of minimal branchement TASK-004 already
  made to both pipelines.
- A new `PEKOPEKO_API_KEY` environment variable joins the bounded `PEKOPEKO_*` set
  TASK-004 established; a new `PEKOPEKO_VAULT_ROOT` environment variable is introduced
  but scoped to the API process only, **not** added to `src/app/config/`'s recognized
  `PEKOPEKO_*` keys (a deliberate asymmetry, per Decision point 4).
- Every future ticket that exposes a new backend capability over HTTP (TASK-015,
  TASK-019, a future config-write endpoint for Settings, etc.) must follow this contract
  rather than introduce a competing one; a deviation (a second framework, a push channel,
  a different auth mechanism) needs its own ADR, not a silent choice inside a ticket.
- The API is unauthenticated beyond the shared key — there is still no per-user identity,
  no role/permission model, and `reviewer_id`/`domain` remain trusted-as-given exactly as
  in every prior ticket. If Pekopeko ever becomes multi-user or leaves the local machine,
  this ADR's security posture must be revisited as its own decision, not assumed to
  still hold.
