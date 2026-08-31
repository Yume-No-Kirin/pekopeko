# TASK-007a: Pagination for List Endpoints (V1)

- **Status**: backlog

## Objective

Extend TASK-007's (`backlog`, not yet implemented) list endpoints — `GET
/domains/<domain>/ingestions`, `GET /domains/<domain>/extractions`, `GET
/domains/<domain>/proposals` — with server-side pagination (`?limit=`/`?offset=`), so
`specs/ux-design/pekopeko-ingestion.html`'s pagination UI (page numbers, "Affichage 1-10
sur 47") can be backed by a real, bounded response instead of a client fetching and slicing
an unbounded full list. Satellite ticket rather than an in-place edit to TASK-007's own
file, specifically so TASK-007's already-written, already-cited acceptance criteria
(TASK-008's plan cites TASK-007 AC12 by number, and future tickets will cite others) keep
their numbering stable — this project's established convention for extending an
already-drafted sibling ticket without reopening it.

## Binding context (references, not duplicated here)

- `specs/tasks/backlog/TASK-007-backend-api-layer.md`: defines the three list endpoints
  this ticket adds pagination to, and the JSON error envelope / `X-API-Key` / CORS /
  `127.0.0.1`-only posture this ticket inherits unchanged.
- ADI-010 (backend-api-layer, Accepted): "no API versioning prefix... single internal
  consumer" — this ticket doesn't reopen that decision, only adds query parameters to
  existing endpoints, matching ADI-010's own closing note that "every future ticket that
  exposes a new backend capability over HTTP... must follow this contract."
- `specs/ux-design/pekopeko-ingestion.html`: pagination controls (`← Précédent`, page
  numbers, `Suivant →`, "Affichage 1-10 sur 47 ingestions") — the concrete UI this ticket
  makes real.
- `specs/tasks/backlog/TASK-009-ingestion-logs-screen.md`,
  `specs/tasks/backlog/TASK-010-validation-screen.md`: both depend on this ticket for real
  server-side pagination instead of client-side slicing of an unbounded list.

## Scope

1. `GET /domains/<domain>/ingestions`, `GET /domains/<domain>/extractions`, `GET
   /domains/<domain>/proposals` each accept optional `limit` (default `50`, integer, `1`
   to `500`) and `offset` (default `0`, integer, `>= 0`) query parameters, applied *after*
   the existing `domain`/`status` filtering TASK-007 already defines.
2. Response shape for all three (uniform, not conditional on whether `limit`/`offset` were
   passed): `{"items": [...], "total": N, "limit": L, "offset": O}` — `items` is exactly
   what TASK-007 already returns as a bare list, `total` is the count *after*
   domain/status filtering but *before* the limit/offset slice, `limit`/`offset` echo the
   effective (possibly defaulted) values used.
3. A stable sort order is applied before slicing, so page N+1 never re-shows or skips items
   relative to page N when the underlying data hasn't changed: `started_at` descending for
   ingestions/extractions, `created_at` descending for proposals (most-recent-first, matching
   the mockup's ordering).
4. `limit`/`offset` outside their valid range (non-integer, `limit` > 500, negative
   `offset`) return `400` with the same JSON error envelope TASK-007 already defines
   (`{"error": {"type": "ValidationError", "message": ...}}`).

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Response envelope change applies uniformly to all three endpoints, always (not only when
  `limit`/`offset` are explicitly passed) — a predictable contract beats a
  conditionally-shaped response. This is a change to TASK-007's originally-sketched bare-list
  response for these three endpoints specifically; TASK-007 itself is amended to reflect
  this once both tickets are implemented together (or TASK-007a's own response shape simply
  supersedes TASK-007's for these three routes if TASK-007 lands first — no other route or
  behavior of TASK-007 is touched).
- No cursor-based pagination — offset/limit is sufficient for a single local user's data
  volumes (matches the personal-scale reasoning already used elsewhere in this backlog,
  e.g. TASK-008's Dashboard aggregation).
- No change to `GET /domains/<domain>/ingestions/<task_id>` (single-item), `GET
  /domains/<domain>/proposals/<proposal_id>` (single-item), or `GET /config` — pagination
  only applies to the three list endpoints named above.
- Default `limit=50` chosen to comfortably exceed the mockup's own "10 per page" example
  while staying well below a size that would make a single response unwieldy at this
  project's scale.

## Requirements

- Python only (ADI-007), Flask (ADI-010) — no new dependency.
- Sorting/slicing happens in `src/app/api/` (the orchestration layer), not inside
  `review/`/`ingestion/`/`extraction/`'s own `list_proposals`/`list_task_states` — those
  keep returning full, unpaginated results; TASK-007a's routes apply sort+slice on top,
  consistent with TASK-007's own "the API layer does no file I/O of its own" posture (this
  is in-memory sort/slice on an already-materialized list, not new I/O).

## Constraints

- No cursor pagination, no change to single-item endpoints or `GET /config`.
- No change to `X-API-Key`/CORS/`127.0.0.1`-only/error-envelope behavior TASK-007 already
  defines — this ticket only adds parameters and reshapes the success response body of
  three routes.
- No new dependency.

## Files/modules concerned

- `src/app/api/routes_ingestion.py`, `routes_extraction.py`, `routes_review.py` (all
  created by TASK-007) — each list route gains `limit`/`offset` parsing/validation,
  sorting, slicing, and the `{items, total, limit, offset}` envelope.
- `src/app/api/serialization.py` (created by TASK-007) — a small shared
  `paginate(items, limit, offset) -> dict` helper, reused by all three routes to avoid
  triplicating the slicing/envelope logic.
- **New tests**: `src/tests/api/` additions covering pagination for all three endpoints
  (parametrized where the three routes' shape is identical enough to share a test
  helper).

## Dependencies

Depends on TASK-007 (`backlog`) existing first — this ticket's routes are edits to files
TASK-007 creates. No dependency on TASK-001a/TASK-001b/TASK-005/TASK-006.

## Acceptance criteria

1. `GET /domains/PERSONAL/ingestions?limit=2&offset=0` on a fixture with 5 ingestion tasks
   returns exactly 2 items, `total: 5`, `limit: 2`, `offset: 0`.
2. The same request with `offset=2` returns the next 2 distinct items (no overlap, no gap,
   relative to the `offset=0` page), confirming stable sort ordering across pages.
3. Omitting `limit`/`offset` entirely returns the same envelope shape with the documented
   defaults (`limit: 50`, `offset: 0`) and `total` equal to the full filtered count.
4. `limit=0`, `limit=501`, or `offset=-1` each return `400` with
   `error.type == "ValidationError"`; no partial/malformed response.
5. Pagination is applied *after* the existing `?status=`/`domain` filtering — a paginated
   response never includes an item that filtering alone would have excluded.
6. Criteria 1-5 hold identically, independently, for `GET .../extractions` and `GET
   .../proposals`.
7. Sort order is `started_at` descending for ingestions/extractions and `created_at`
   descending for proposals — verified against a fixture with known, distinct timestamps.
8. No change to the response shape or behavior of the single-item endpoints or `GET
   /config` — regression coverage confirming TASK-007's own tests for those routes still
   pass unmodified.

## Testing requirements

`pytest`, Flask's `app.test_client()`, `tmp_path` fixtures with multiple ingestion/
extraction/proposal records of known, distinct timestamps to make ordering assertions
unambiguous. Minimum: one test per acceptance criterion above (8 total, with criterion 6
effectively tripling coverage of 1-5 across the three endpoints).

## Out of scope

- Cursor-based pagination.
- Pagination of single-item endpoints or `GET /config`.
- Any GUI — TASK-009/TASK-010 consume this ticket's output, implemented separately.
- Changing `review.list_proposals`/`*.list_task_states`' own Python signatures — they stay
  as TASK-007 already defines them; pagination lives entirely in the `api/` orchestration
  layer.
