# TASK-009: Ingestion Logs Screen (V1)

- **Status**: backlog

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
