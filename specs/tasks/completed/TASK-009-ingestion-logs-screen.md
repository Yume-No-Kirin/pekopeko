# TASK-009: Ingestion Logs Screen (V1)

- **Status**: completed

## Objective

Implement `pekopeko-ingestion.html` (`specs/ux-design/`) as a React screen: a filterable,
paginated table of ingestion and extraction tasks, with per-task error/duplicate/event
detail — making the work TASK-001/TASK-003 already produce (`completed`) visible for the
first time. Second screen of the GUI socle after TASK-008 (Dashboard/Settings scaffold,
`backlog`), consuming TASK-007's API (`backlog`) plus two satellite extensions written
alongside this ticket: TASK-007a (server-side pagination) and TASK-001b (per-task event
log). Full fidelity to the mockup's table, filters, pagination, and log detail — no feature
silently dropped for lack of backend data; where the backend doesn't have it yet, a
satellite ticket supplies it (see Dependencies).

## Binding context (references, not duplicated here)

- `specs/decisions/ADI-009-frontend-framework.md` / `ADI-010-backend-api-layer.md`: React,
  Flask/REST, `X-API-Key`, domain-scoped endpoints.
- `specs/tasks/backlog/TASK-008-react-scaffold-dashboard-settings.md`: provides the
  routing shell (`App.jsx`), `api/client.js` (base URL + `X-API-Key` + `ApiError`
  parsing), `api/domains.js` (fixed 5-domain list), `Sidebar.jsx` — this ticket adds a
  route and a page, reusing all of it, and flips the Dashboard's "Logs d'ingestion" module
  card from `coming-soon` to `available`.
- `specs/tasks/backlog/TASK-007-backend-api-layer.md`: `GET
  /domains/<domain>/ingestions`/`.../extractions` (optional `?status=`), `TaskState` JSON
  shape (`task_id, source_path, domain, status, started_at, completed_at, error, source_id,
  proposal_ids`).
- `specs/tasks/backlog/TASK-007a-list-endpoint-pagination.md`: adds `?limit=`/`?offset=`
  and the `{items, total, limit, offset}` envelope to the two list endpoints this screen
  uses — this ticket's pagination UI is built against that envelope, not a bare array.
- `specs/tasks/backlog/TASK-001b-task-event-log.md`: adds `events: list[TaskEvent]`
  (timestamp/level/message/details) to `TaskState` — this ticket's log-detail panel
  renders that list.
- `specs/ux-design/pekopeko-ingestion.html`: table columns, filters (status/domain/period),
  pagination controls, "Voir logs"/"Voir erreur"/"Voir original" action links.
- `specs/domain/knowledge-invariants.md` INV-008/INV-009: every list endpoint is
  domain-scoped — a "tous les domaines" view is a client-side aggregation across the 5
  fixed domains, per the same pattern TASK-008 already established for the Dashboard, not
  a new cross-domain backend capability.

## Scope

New route `/ingestion-logs`, new page `frontend/src/pages/IngestionLogs.jsx`.

1. **Data fetch**: in parallel, for each of the 5 fixed domains, `GET
   /domains/<d>/ingestions` and `GET /domains/<d>/extractions` (paginated per
   TASK-007a — see "Pagination strategy" below), merged into one client-side list, each
   row tagged with its task type (`ingestion`/`extraction`).
2. **Table** — one row per task: Source (basename of `source_path`, plus `source_id` once
   resolved), Domaine, Type (ingestion/extraction), Statut (badge:
   `pending/running/completed/failed/skipped_duplicate`), Démarré (`started_at`), Complété
   (`completed_at`, em-dash if null), Propositions (`proposal_ids.length`), Actions.
3. **Filters**: Statut, Domaine, Période — Statut/Domaine reflect in the underlying fetch
   (re-scope which domains/status are requested); Période is client-side only on
   `started_at` (no date-range query parameter exists in TASK-007/TASK-007a).
4. **Row detail** ("Voir logs" / "Voir erreur" / "Voir original"): an inline
   expand/accordion (no separate route — `TaskState` has nothing that justifies a
   dedicated page) showing, per task:
   - the full `events` list from TASK-001b (timestamp, level badge, message, `details`),
     matching the mockup's "Logs d'ingestion complets" entries;
   - for a `failed` task, the `error` string is also shown prominently above the event
     list (both are shown — `error` is the terse summary, `events` is the trace);
   - for a `skipped_duplicate` task, the event list's duplicate-detection entry (from
     TASK-001b) surfaces the original `source_id`, satisfying "Voir original".
5. **Pagination**: real, server-side, via TASK-007a's `{items, total, limit, offset}`
   envelope per domain/type — see "Pagination strategy" below for how per-domain pages are
   combined into one cross-domain, cross-type table.
6. **Dashboard update** (part of this ticket, not a separate one): the "Logs d'ingestion"
   module card on `frontend/src/pages/Dashboard.jsx` (TASK-008) switches from
   `coming-soon`/non-clickable to `available`, linking to `/ingestion-logs`.

### Pagination strategy (cross-domain, cross-type, server-paginated pages)

TASK-007a paginates *per domain, per endpoint* — there is no single server-side page
across all 5 domains × 2 task types. This screen's pagination therefore works as follows:
for the currently active filters (domain filter narrows which of the 5 domains are
queried; "all domains" queries all 5), fetch page 0 (`offset=0`, the configured page size)
from every in-scope domain/type combination in parallel, merge and re-sort the merged set
client-side (`started_at` descending, matching TASK-007a's own per-request ordering so the
merge is stable), and display the requested page size from the top of that merged set;
advancing to the next page re-fetches with a proportionally advanced `offset` per
domain/type source and repeats the merge. This is real server-side pagination per request
(bounded response sizes, matching TASK-007a's intent) composed client-side across the
fixed 5-domain/2-type fan-out — not a full unbounded fetch followed by client slicing.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No dedicated "task detail" page/route — the mockup's per-row "Voir logs" is served by an
  inline expand, since `TaskState`+`events` (TASK-001b) is a small, single-task payload
  with nothing that justifies full-page navigation.
- Période filter is client-side only (no backend date-range parameter exists) — filters the
  already-fetched merged page, not a separate server round-trip.
- "Nouvelle ingestion" button from the mockup: out of scope here — no endpoint exists to
  start an ingestion from an arbitrary user-supplied path outside a pre-existing local
  file the API process can already read; deferred, not part of this ticket's Dependencies
  (no satellite proposed for it — flagging it here rather than silently building a
  non-functional button).

## Requirements

- Every outgoing request goes through `frontend/src/api/client.js` (TASK-008) — new
  `frontend/src/api/tasks.js` wrapper for ingestion/extraction list+pagination calls,
  reused later by TASK-010/TASK-011 where relevant (source→task join).
- No ad hoc `fetch()` calls outside the `api/` wrappers.

## Constraints

- No new backend endpoint invented by this ticket itself — all data comes from TASK-007 +
  TASK-007a + TASK-001b, cited as dependencies.
- No "start a new ingestion" action (see V1 scope decisions).
- No modification to any file under `src/` — this ticket is `frontend/`-only.

## Files/modules concerned

- **New**: `frontend/src/pages/IngestionLogs.jsx`.
- **New**: `frontend/src/api/tasks.js` — `listIngestions(domain, {status, limit, offset})`,
  `listExtractions(domain, {...})`, both returning the `{items, total, limit, offset}`
  envelope, built on `api/client.js`.
- **New**: `frontend/src/components/TaskStatusBadge.jsx`,
  `frontend/src/components/TaskEventLog.jsx` (renders one task's `events`, reused nowhere
  else in this ticket but shaped for reuse by TASK-011's log section).
- **Modified**: `frontend/src/App.jsx` (new `/ingestion-logs` route), `frontend/src/pages/
  Dashboard.jsx` (module card flips to `available`).
- **New tests**: `frontend/src/pages/IngestionLogs.test.jsx`,
  `frontend/src/api/tasks.test.js`.

## Dependencies

Depends on TASK-007 (`backlog`), TASK-007a (`backlog`, pagination), TASK-001b (`backlog`,
event log), and TASK-008 (`backlog`, shell/routing). Independent of TASK-005/TASK-006/
TASK-001a/TASK-010/TASK-011.

## Acceptance criteria

1. The table renders merged ingestion + extraction rows across the 5 fixed domains by
   default, each row correctly tagged with its type.
2. Status/Domain filters correctly narrow which rows are fetched/shown; Period filters the
   already-fetched set client-side on `started_at`.
3. A `failed` row's expanded detail shows both its `error` string and its full `events`
   sequence from TASK-007a's/TASK-001b's response.
4. A `skipped_duplicate` row's expanded detail surfaces the original `source_id` via its
   `events` entry.
5. Pagination controls request the next/previous page via `?limit=`/`?offset=` (mocked
   `fetch` asserts the correct query parameters) and the displayed "Affichage X-Y sur Z"
   count matches the merged `total`.
6. Switching the Domain filter re-scopes which domains are queried (mocked `fetch` shows
   fewer domain calls when one domain is selected vs. "tous les domaines").
7. Every outgoing request carries `X-API-Key` (inherited via `api/client.js`, verified for
   at least one call this ticket adds).
8. The Dashboard's "Logs d'ingestion" module card is `available` and navigates to
   `/ingestion-logs`.
9. A loading state and an error state (mocked rejected `fetch`/`401`) render without
   crashing.
10. No file under `src/` is modified by this ticket.

## Testing requirements

Vitest + React Testing Library, `fetch` fully mocked, no real network calls, no dependency
on a running Flask instance. Minimum: one test per acceptance criterion above (10 total).
Coverage discipline (≥80%) applies to `frontend/src/pages/IngestionLogs.jsx` and
`frontend/src/api/tasks.js`.

## Out of scope

- "Nouvelle ingestion" (start-ingestion) action — no backend capability exists or is
  proposed for it here (see V1 scope decisions).
- A dedicated per-task detail route/page.
- Server-side date-range filtering.
- Any change to `src/`.

## Deviations from the ticket text (flagged, not silent)

- **`frontend/src/components/Sidebar.jsx` modified**, though not in this ticket's own
  "Files/modules concerned" list. Flipping the Dashboard's module card to `available`
  without also promoting the sidebar's "Logs ingestion" entry out of the disabled "Modules
  à venir" section would leave a reachable page permanently greyed out in the persistent
  nav — an inconsistent state, not a scope boundary worth preserving. Mirrors exactly how
  TASK-008 already listed Settings under "Modules actifs". Confirmed with Cleo before
  implementing.
- **Mockup fidelity, two simplifications, both confirmed with Cleo before implementing**:
  the mockup's numbered 1-5 page-button row is not ported (Prev/Next + the "Affichage X-Y
  sur Z" count satisfies every acceptance criterion; a true page count isn't cleanly
  knowable across the 10-source domain/type fan-out this screen's pagination composes
  across). The header's "+ Nouvelle ingestion" button is not ported (explicitly out of
  scope above — no backend capability exists to back it). The header's "↻ Rafraîchir"
  button **is** ported (`.btn`, re-runs the current fetch for the active page/filters via a
  `refreshKey` counter) — Cleo asked for it to be kept despite it being outside the
  ticket's own Scope items 1-6.

## Implementation notes

- `frontend/src/api/tasks.js`: `listIngestions(domain, {status, limit, offset})` /
  `listExtractions(domain, {...})`, thin wrappers over `api/client.js::get`, returning the
  raw `{items, total, limit, offset}` envelope untouched.
- `frontend/src/components/TaskStatusBadge.jsx` / `TaskEventLog.jsx`: both generic over the
  ingestion/extraction `TaskState`/`TaskEvent` shape (identical in both backend modules per
  `src/app/ingestion/task_state.py` and `src/app/extraction/task_state.py`), no
  type-specific branching — `TaskEventLog` is reused verbatim by this ticket's own
  row-detail accordion and is shaped for TASK-011 to reuse for its own log section.
- `frontend/src/pages/IngestionLogs.jsx`: implements the ticket's "Pagination strategy"
  section literally — per active filters, fans out to every in-scope domain × type
  combination (`Promise.all`) with the same `limit`/proportionally-advanced `offset`,
  merges, sorts descending by `started_at`, and takes the top `pageSize` (10, matching the
  mockup's "1-10") as the displayed page; `total` is the sum of each source's own `total`.
  Row-detail expansion needs no extra fetch — `events` already comes back on every list-item
  (TASK-001b), so there's no N+1 here unlike Dashboard's/Validation's proposal-detail joins.
  Period filtering is client-side only, applied to the already-fetched page, per the
  ticket's own explicit V1 decision.
- `frontend/src/index.css`: ported the ingestion mockup's `.filters-bar`/`.filter-*`/
  `.table*`/`.status-badge*`/`.domain-badge`/`.action-link`/`.pagination*`/`.empty-state*`/
  `.file-name`/`.source-id`/`.header-actions`/`.btn` blocks verbatim. Added `.page-header
  .with-actions` as a *modifier* class (not a redefinition of the shared `.page-header`) so
  Dashboard/Settings' non-flex, stacked headers are unaffected. Added new, mockup-absent
  classes for the Type column badge and the row-detail accordion
  (`.task-error`/`.task-event-log`/`.task-event*`), in the same visual language as the rest
  of the file.

## Verification record

- `cd frontend && npm run build` — completes without error, produces `dist/index.html` +
  `dist/assets/*` (build wiring, all new imports resolve).
- `npx vitest run` — 25/25 tests pass: `client.test.js` (2, pre-existing), `tasks.test.js`
  (3, new), `Settings.test.jsx` (3, pre-existing), `Dashboard.test.jsx` (9 — 7 pre-existing
  + 1 updated in place for the now-available Ingestion Logs card + 1 new end-to-end
  navigation test), `IngestionLogs.test.jsx` (8, one per AC1-7/9 — AC8 covered by
  `Dashboard.test.jsx`, AC10 verified below, not a runtime assertion).
- `npx vitest run --coverage` — 98.41% statements/lines overall; `api/tasks.js` 100%
  statements/lines/branches/functions; `pages/IngestionLogs.jsx` 100% statements/lines,
  90.54% branches, 87.5% functions — all comfortably above the project's 80% floor
  (`vite.config.js`'s `coverage.thresholds`, which gates the run).
- `grep -rn "fetch(" frontend/src --include=*.js --include=*.jsx` — only match is
  `frontend/src/api/client.js` (Requirements: "No ad hoc fetch() calls outside the api/
  wrappers").
- `git status --porcelain -- src/` — empty after this ticket's changes (AC10).
- Acceptance criteria 1-9 verified directly by the Vitest suites named above (one test per
  criterion, see `IngestionLogs.test.jsx` test names); AC8 by `Dashboard.test.jsx`'s two
  Ingestion Logs tests (module-card `available`+`href`, and an end-to-end click-through
  navigation test rendering `IngestionLogs` at `/ingestion-logs`); AC10 by the `git status`
  command above.
- Not independently re-verified by a second reviewer (same limitation as every prior ticket
  in this project) — nor smoke-tested against a real running Flask instance in a browser
  (no local vault/API process available in this session); recommended as a follow-up manual
  check before this screen is relied on operationally. The merge-based pagination strategy
  in particular (approximate by design per the ticket's own text) would benefit from a
  manual check against a vault with >10 tasks in a single domain/type to confirm the
  merge/sort/slice behaves as intended end-to-end.
