# TASK-019: Search Screen (frontend)

- **Status**: backlog

## Objective

Sixth screen on the existing React frontend (`frontend/`, built by TASK-008 and extended by
TASK-009/010/011/013/014), consuming TASK-018's `GET /domains/<domain>/search` endpoint. Turns the
Dashboard's `Recherche` module card (`frontend/src/pages/Dashboard.jsx:151-155`) from a
`coming-soon` placeholder into a working screen at `/search` — the same `status`/`to` mechanism
already used for the Validation/Ingestion Logs/Settings cards.

Did not exist under any ID in `specs/tasks/BACKLOG-CLAUDE.md` (retrieval was backend-only there);
created as a new entry specifically by `BACKLOG-CLAUDE-V2.md`'s GUI-first re-prioritization.
Written directly at Cleo's request rather than in strict backlog order — TASK-015 remains the next
ticket scheduled for *implementation* (see `docs/ROADMAP.md`).

No canonical-item detail screen exists anywhere in the frontend yet — TASK-011/012's
`ProposalDetail.jsx` covers a *proposal* (pre-acceptance review queue), not an accepted canonical
item. This screen is therefore the first place a user can see canonical knowledge at all after it
leaves the review queue, and it has nowhere to link a result to. It must show enough on its own
(TASK-018 already returns each result's full `body`, not only a snippet, for exactly this reason)
via inline expansion, not by navigating to a detail route that doesn't exist.

## Binding context (references, not duplicated here)

- `specs/ux-design/pekopeko-dashboard.html`/`specs/ux-design/README.md`: the only existing UX
  trace for this screen is the `Recherche` module card's placeholder text ("Recherche full-text et
  sémantique dans la base de connaissances, avec filtres par domaine et type") — no dedicated
  mockup exists, unlike TASK-009/010/011. This ticket is not bound to pixel-level mockup fidelity;
  it should still visually match the existing screens (reusing their layout/badge components).
- `specs/tasks/backlog/TASK-018-local-retrieval-index.md`: the exact contract this screen consumes
  — `GET /domains/<domain>/search?q=&item_type=&context=&limit=&offset=` →
  `{items: [{id, item_type, domain, context, epistemic_status, lifecycle_status, path_segments,
  snippet, body}], total, limit, offset}`.
- **ADI-016** (`specs/decisions/ADI-016-context-universe-first-class-field.md`, Accepted) and
  **TASK-014a** (`backlog`): the `context` field this screen filters on. See Scope §1 and
  TASK-018's own "Relation to ADI-016/TASK-014a" section for why this matters *here* specifically.
- `frontend/src/api/client.js` (`get`, `buildListUrl`, `ApiError`) and
  `frontend/src/api/review.js` (thin per-resource wrapper pattern) — `frontend/src/api/search.js`
  follows the same shape.
- `frontend/src/App.jsx`: existing `react-router-dom` routes (`/`, `/settings`,
  `/ingestion-logs`, `/validation`, `/validation/:domain/:proposalId`) — this ticket adds `/search`
  the same way.
- Existing reusable components from TASK-010/012: `EntityTypeBadge`, `EpistemicStatusBadge` (and
  any other status-badge component already used in `Validation.jsx`/`ProposalDetail.jsx`) — reused
  to render each result's `item_type`/`epistemic_status`/`lifecycle_status` rather than inventing
  new badge styles.

## Scope

1. New page `frontend/src/pages/Search.jsx`:
   - A text input for the query (`q`) and a required domain selector (same constraint as every
     other screen in this frontend — no cross-domain view).
   - An optional `item_type` filter (`assertion`/`entity`/`event`/`relationship`/"all").
   - An optional `context` filter (free text, or a select populated from the `context` values
     present in the current result set — implementer's choice, document whichever is chosen).
     **Not cosmetic**: this screen is the first place in the product where canonical knowledge is
     visible at all (see Objective), so without it two novels sharing a character name are
     displayed intermixed with no way to separate them — the exact scenario UC-018 ("Fictional
     Universe Isolation") describes and ADI-016 exists to address. `domain` cannot substitute for
     it: both novels live in the same `FICTION` domain.
   - Submitting (on input debounce or explicit submit — implementer's choice, document whichever
     is chosen) calls `search(domain, { q, itemType, limit, offset })` via the new
     `frontend/src/api/search.js`.
   - Paginated results using the existing `buildListUrl`/`limit`/`offset` convention, with a
     "page N, showing X-Y of Z" style control matching `IngestionLogs.jsx`/`Validation.jsx`'s
     existing pagination UI.
2. Result rendering, one row/card per item:
   - `item_type`, `domain`, `epistemic_status`, `lifecycle_status` via the existing badge
     components. Note that `lifecycle_status` is `ACTIVE` for every canonical item today (only
     `history/` snapshots carry `SUPERSEDED`, and TASK-018 does not index those) — the badge is
     therefore constant until supersession of canonical items exists (`BACKLOG-CLAUDE-V2.md`'s
     TASK-022). Rendered anyway for forward-compatibility, not because it currently distinguishes
     anything; do not spend design effort on it.
   - `context` when present (a small chip next to the domain badge), so a result's universe/project
     is readable at a glance and not only via the filter.
   - The `snippet` (already highlighting the matched term, produced server-side by TASK-018's
     FTS5 `snippet()`), rendered as-is.
   - An expand/collapse affordance that reveals the already-fetched `body` in full — no additional
     network request, no navigation to a detail route (see Objective).
3. Loading and error states matching `Validation.jsx`/`IngestionLogs.jsx`'s existing conventions:
   a loading skeleton/indicator while the request is in flight, and a readable error message
   (not a blank/broken screen) when the request rejects with an `ApiError`.
   Plus one static, always-visible note near the results header stating that the index is rebuilt
   at API startup, so an item accepted during the current session may not appear until the server
   is restarted (TASK-018's V1 refresh model). A one-line honest statement, not a freshness
   timestamp — the API exposes no such value, and this ticket adds no backend surface (see
   Constraints). Remove it if and when TASK-018's staleness question is resolved in the other
   direction.
4. `frontend/src/pages/Dashboard.jsx`: the `Recherche` `ModuleCard` (lines 151-155) gets
   `status="available"` and `to="/search"`, matching the Validation/Ingestion Logs/Settings cards
   exactly.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **No dedicated canonical-item detail screen.** Inline expansion inside the results list is the
  V1 mechanism (see Objective). A real per-item detail view (its own route, richer metadata
  display, maybe deep-linkable) is a candidate future ticket if Cleo wants one once this screen is
  in use.
- **No semantic search UI** — the screen only ever exposes what TASK-018 provides (full-text via
  FTS5); no "smart search" affordance implying capabilities that don't exist yet.
- **One domain at a time**, matching every other screen in this frontend — no "all domains"
  aggregate search option.
- **The `context` filter reads, never writes.** Editing an item's `context` happens in
  `ProposalDetail.jsx`'s edit mode (TASK-014a), pre-acceptance; nothing on this screen changes a
  canonical item (no canonical-item write path exists anywhere in the API today).

## Requirements

- Matches the existing frontend stack exactly: React, `react-router-dom`, Vite, no new state
  management library (plain hooks/local state, same as `Validation.jsx`).
- `frontend/src/api/search.js` uses the existing `get`/`buildListUrl` helpers from `client.js` —
  no separate fetch logic.

## Constraints

- No backend changes — this ticket is frontend-only, consuming TASK-018's already-defined
  contract as-is. If the contract turns out to be insufficient, that's a TASK-018 amendment to
  flag, not a workaround to build here.
- No change to any other existing page/route beyond the `Recherche` card's `status`/`to` on
  `Dashboard.jsx`.

## Files/modules concerned

- **New**: `frontend/src/pages/Search.jsx`, `frontend/src/pages/Search.test.jsx`.
- **New**: `frontend/src/api/search.js`, `frontend/src/api/search.test.js`.
- **Modified**: `frontend/src/App.jsx` — new `/search` route.
- **Modified**: `frontend/src/pages/Dashboard.jsx` — `Recherche` card's `status`/`to` (and its
  own `Dashboard.test.jsx` updated for the new card state).

## Dependencies

Depends on TASK-018 (backend, `backlog`) existing first — this ticket's `api/search.js` is a
thin wrapper around TASK-018's exact response shape. Soft-coupled to TASK-014a (`backlog`) for the
`context` field, exactly as TASK-018 is: the filter and chip degrade to "no item has a context" and
every other acceptance criterion still holds (AC9). Independent of TASK-015/TASK-016/TASK-017.

## Acceptance criteria

1. Entering a query and choosing a domain triggers a `GET /domains/<domain>/search?q=...` call
   (via a mocked `fetch`/`client.js` in tests) and renders the returned items.
2. Changing the `item_type` filter re-issues the search with the corresponding `item_type` query
   parameter.
3. Paging controls use `limit`/`offset` and reflect the `total` returned by the API (e.g. "showing
   X-Y of total").
4. Expanding a result reveals its full `body` content without any additional network request and
   without changing the route.
5. A rejected request (`ApiError`) renders a readable error message instead of a blank or crashed
   screen.
6. The Dashboard's `Recherche` card no longer shows "À venir"/`coming-soon` styling and navigates
   to `/search` on click.
7. No query and/or no domain selected does not trigger a request (mirrors TASK-018's own
   `q`-required validation, checked client-side before calling the API).
8. Changing the `context` filter re-issues the search with the corresponding `context` query
   parameter; clearing it re-issues the search with no `context` parameter at all (not an empty
   one). A fixture with two items differing only by `context` confirms only the matching one is
   rendered.
9. A result carrying a `context` renders its chip; one with `context: null` renders no chip and no
   empty placeholder — the screen must work unchanged against a vault predating TASK-014a.

## Testing requirements

Vitest + React Testing Library, matching `Validation.test.jsx`/`IngestionLogs.test.jsx`'s existing
conventions (mocked `client.js`, no real network calls). Minimum: one test per acceptance
criterion above (9 total). Coverage ≥80% on `Search.jsx` and `api/search.js`.

## Out of scope

- Semantic/embedding search UI.
- A dedicated canonical-item detail screen/route.
- Cross-domain search.
- Any backend work — fully covered by TASK-018.
