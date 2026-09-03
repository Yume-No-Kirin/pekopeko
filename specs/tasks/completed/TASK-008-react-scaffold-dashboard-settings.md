# TASK-008: React Scaffold, Dashboard and Settings Screens (V1)

- **Status**: completed

## Objective

Stand up the first frontend code Pekopeko has ever had: a React project (build tooling,
routing, component structure — the exact scope ADI-009 left open, "once that work is
actually scoped") consuming the API of TASK-007 (`specs/tasks/backlog/TASK-007-backend-api-layer.md`,
also `backlog`). Delivers two screens: `pekopeko-dashboard.html` (overview stats + module
cards, per `specs/ux-design/`) and a new Settings screen (not in the mockups, requested
explicitly by Cleo) that displays the local configuration from TASK-004, read-only.
Mandatory prerequisite for TASK-009 through TASK-012 in the same GUI socle
(`specs/tasks/BACKLOG-CLAUDE-V2.md` section 1): the routing/component shell built here is
what those later tickets add screens to. Corresponds to the old `TASK-021` (V1 framing) +
`TASK-023` (Dashboard) of `specs/tasks/BACKLOG-CLAUDE.md`, plus the Settings screen that
existed in neither prior backlog version.

New code only, in a new top-level `frontend/` directory (sibling of `src/`, not nested
inside it — keeps the Python/Node ecosystems from mixing under the same tree). No change
to any file under `src/`.

## Binding context (references, not duplicated here)

- **ADI-009** (frontend-framework, Accepted): React chosen; build tooling, routing, and
  state management explicitly left open for this ticket to decide — this ticket makes
  those decisions (see V1 scope decisions), it does not re-open the framework choice.
- **ADI-010** (backend-api-layer, Accepted) / **TASK-007**: every request must carry
  `X-API-Key`; `domain` is a required path segment on every ingestion/extraction/review
  endpoint (INV-008/INV-009); the JSON error envelope is
  `{"error": {"type": ..., "message": ...}}`; polling only, no push channel; `GET /config`
  is the only config endpoint (no write).
- `specs/ux-design/README.md` and `pekopeko-dashboard.html`: sidebar navigation shell
  (Principal / Modules actifs / Modules à venir), 4 stat cards, a module-card grid with
  `available`/`coming-soon` badges. The stat card for canonical knowledge is captioned
  "Tous domaines confondus" in the mockup itself — the only textual signal in the corpus
  that Dashboard stats aggregate across all 5 domains rather than showing one selected
  domain (no domain selector appears anywhere in the mockups). "No real-time updates
  (manual refresh workflow)" (same README) — no polling in this ticket.
- `specs/tasks/completed/TASK-004-local-configuration.md`: `PekopekoConfig` fields
  (`llm_provider.active`, `retrieval.index_dir`, `task_state.dir`, `default.domain`) and
  its explicit V1 decision "No CLI or GUI for editing configuration — a hand-edited YAML
  file is sufficient for V1" — still true after this ticket; Settings only reads.
- `specs/domain/knowledge-invariants.md` INV-011: a GUI is a representation, not the
  canonical model — this ticket renders only what the API already projects, no new
  persistence or derived storage of its own.

## Scope

New project `frontend/`:

1. **Build tooling and routing** — Vite + React (plain JavaScript/JSX, not TypeScript —
   no requirement in the corpus justifies the added complexity) + React Router
   (`BrowserRouter`), with two routes: `/` (Dashboard) and `/settings` (Settings). Routing
   structure is built so TASK-009/010/011 only need to add a route + page component, not
   restructure `App.jsx`.
2. **API client** (`frontend/src/api/client.js`) — a single `fetch` wrapper used by every
   page: prefixes `VITE_API_BASE_URL` (default `http://127.0.0.1:5000`), attaches
   `X-API-Key: <VITE_API_KEY>` on every request, and on a non-2xx response parses the
   `{"error": {"type", "message"}}` envelope into a typed JS `ApiError` (`type`,
   `message`, `status`) instead of letting callers parse raw JSON ad hoc.
3. **Domain enum** (`frontend/src/api/domains.js`) — the same fixed 5-value list
   (`PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING`) re-declared on the JS side,
   matching the project's established "no module imports another's internals for shared
   constants" convention (already applied by `src/app/api/domains.py` in TASK-007).
4. **Sidebar shell** (`frontend/src/components/Sidebar.jsx`) — ported from
   `pekopeko-dashboard.html`'s sidebar markup/sections, shared by every page.
5. **Dashboard** (`frontend/src/pages/Dashboard.jsx`) — 4 stat cards + module-card grid
   (see "Dashboard stats" and "Dashboard module cards" below).
6. **Settings** (`frontend/src/pages/Settings.jsx`) — read-only view of `GET /config`'s
   4 fields plus a static help note (see "Settings screen" below).

### Dashboard stats (V1, client-side aggregation — no aggregate endpoint exists)

TASK-007 exposes no cross-domain aggregate or canonical-count endpoint. Every list request
below returns TASK-007a's `{items, total, limit, offset}` envelope; every pure count (not
needing individual item fields) sums the `total` field across domains — never `items.length`
— so it stays correct even when a domain's matching items exceed TASK-007a's default
`limit=50` page size. For each of the 5 fixed domains, in parallel (`Promise.all`):

- **Ingestions en cours** — `GET /domains/<d>/ingestions?status=pending` and
  `?status=running`, `total` summed across all 5 domains for each status, then added
  together. Scoped to ingestion tasks only (the mockup label says "Ingestions", not
  "Ingestions + Extractions"); extraction task visibility is TASK-009's concern (Ingestion
  Logs screen).
- **Propositions en attente** — `GET /domains/<d>/proposals?status=PROPOSED`, `total`
  summed across domains.
- **Connaissances canoniques** — approximated as the sum of `total` from `GET
  /domains/<d>/proposals?status=ACCEPTED` across domains. Documented explicitly as
  an approximation (no canonical-item-count endpoint exists and none is added by this
  ticket): each accepted proposal produces exactly one canonical item 1:1
  (`accept_proposal`'s existing contract), so the count stays accurate even once TASK-005
  lands (entity/event/relationship proposals go through the same `accept_proposal`
  status transition).
- **Taux d'acceptation (30 derniers jours)** — unlike the counts above, this stat needs
  individual `reviewed_at` values, not just `total`, so it reuses the `items` array from
  the same per-domain `ACCEPTED` fetch above plus a parallel `REJECTED` fetch, filtering
  client-side on `reviewed_at` within the last 30 days, then
  `accepted / (accepted + rejected)`. Bounded by TASK-007a's default `limit=50` per
  domain/status — documented as a V1 approximation, consistent with the other approximated
  stats on this screen: at this project's personal scale, more than 50 review decisions per
  domain in 30 days is not expected, and extending this to a fully accurate count (e.g. via
  a higher `limit` or a dedicated aggregate endpoint) is future work if it ever proves
  insufficient. If the denominator is 0, render "—" rather than dividing by zero.
- Single fetch on mount, no polling/auto-refresh (per `specs/ux-design/README.md`).
- A loading state (skeleton/placeholder) while the 5×N requests are in flight, and an
  error state (API unreachable, or a `401 ApiError`) that renders a message instead of
  crashing the page.

### Dashboard module cards

Reuses the mockup's module-card grid, but reflects what actually exists after *this*
ticket, not the mockup's end-state: Validation and Ingestion Logs render with the
`coming-soon` badge and are not clickable (their screens are TASK-009/TASK-010, not built
yet); a new Settings card renders `available` and links to `/settings`. Analytics/Export/
Recherche stay `coming-soon`, unchanged from the mockup. No dead links.

### Settings screen (read-only)

Renders, from `GET /config`: active LLM provider (`llm_provider.active`), default domain
(`default.domain`), retrieval index location (`retrieval.index_dir`), task-state location
(`task_state.dir`) — the 4 fields TASK-007's Acceptance Criterion 12 guarantees are
present. Below the fields, a static help note names the local config file's default
resolved path (`~/.pekopeko/config.yaml`, plus the optional companion `~/.pekopeko/.env`)
and states that editing is done by hand in that file — hardcoded text, not fetched from
the API (the API has no endpoint that returns the config *file path*, only its parsed
contents). No editable form field, no save button, no write request anywhere on this
screen — matches Cleo's explicit decision (2026-08-31): Settings stays read-only for V1;
a config-write endpoint is a separate future ticket if the need becomes real.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **API key delivery** (Cleo, 2026-08-31): a build-time environment variable
  (`VITE_API_KEY`, from a local, uncommitted `frontend/.env`), baked into the JS bundle at
  build time. No runtime prompt, no `localStorage` flow. Consistent with ADI-010's
  security posture (single local user/device, not a real multi-tenant secret).
- **Settings is read-only** (Cleo, 2026-08-31) — see "Settings screen" above. The backlog
  entry's wording ("visualise/édite") is superseded by this explicit decision; a
  config-write endpoint is out of scope here.
- **No TypeScript** — plain JS/JSX, avoiding an additional toolchain decision the corpus
  never asked for.
- **No global state management library** (Redux/Zustand/etc.) — two pages, each owning
  its own local fetch/state; not justified at this scale.
- **No domain selector in the UI** — Dashboard aggregates across the 5 fixed domains
  (per the mockup's own "Tous domaines confondus" caption); no per-domain view exists yet
  anywhere in the GUI at this stage.
- **No end-to-end/browser test tooling** (Playwright/Cypress) — Vitest + React Testing
  Library only, matching this ticket's scope; introduce E2E tooling later if a ticket
  needs it.

## Requirements

- Node/npm-based tooling (Vite, React, React Router) — first Node dependency in this
  repository; no interaction with `src/requirements.txt` or any Python tooling.
- `frontend/.env.example` documents `VITE_API_BASE_URL`/`VITE_API_KEY` with placeholder
  values only; the real `frontend/.env` is gitignored, never committed.
- No git usage inside application code (project-wide constraint) — irrelevant to a static
  frontend build beyond the existing repository-level `.gitignore` entry for `frontend/.env`.
- Every outgoing API request goes through the single `api/client.js` wrapper — no ad hoc
  `fetch()` calls scattered across components (keeps the `X-API-Key` header and error
  envelope handling in one place for TASK-009 onward to reuse).

## Constraints

- No config write endpoint or write UI (see V1 scope decisions).
- No domain selector, no per-domain Dashboard view.
- No canonical-count or aggregate backend endpoint added — approximated client-side only,
  as documented above.
- No polling/live updates.
- No TypeScript, no global state management library, no E2E test tooling.
- No modification to any file under `src/` (this ticket is additive, `frontend/` only).

## Files/modules concerned

- **New**: `frontend/package.json`, `frontend/vite.config.js`, `frontend/index.html`,
  `frontend/.env.example`, `frontend/.gitignore` (excludes `.env`, `node_modules`,
  `dist`).
- **New**: `frontend/src/main.jsx` — React entry point, mounts `<App />`.
- **New**: `frontend/src/App.jsx` — `BrowserRouter` + route table (`/`, `/settings`).
- **New**: `frontend/src/api/client.js` — `fetch` wrapper (base URL, `X-API-Key` header,
  `ApiError` parsing from the `{"error": {...}}` envelope).
- **New**: `frontend/src/api/domains.js` — the re-declared fixed 5-domain list.
- **New**: `frontend/src/components/Sidebar.jsx`, `StatCard.jsx`, `ModuleCard.jsx`.
- **New**: `frontend/src/pages/Dashboard.jsx`, `Settings.jsx`.
- **New tests**: `frontend/src/api/client.test.js`, `frontend/src/pages/Dashboard.test.jsx`,
  `frontend/src/pages/Settings.test.jsx` (Vitest + React Testing Library, `fetch` mocked).
- **No changes** to `src/app/*` or `src/tests/*`.

## Dependencies

Depends on TASK-007 (`backlog`) for the API contract this ticket's `api/client.js` and
pages are written against — cannot be implemented (though it can be reviewed/scaffolded)
before TASK-007 lands. **Also depends on TASK-007a (`backlog`, pagination envelope)**: the
Dashboard's stat-card counts (Criteria 5-7) read `GET .../ingestions?status=` and
`GET .../proposals?status=`, two of the three endpoints TASK-007a wraps in a
`{items, total, limit, offset}` envelope with `limit` defaulting to 50 — this ticket's
counting logic must be written against that envelope (summing `total`, not `items.length`)
from the start, so it stays correct once a domain's item count exceeds the default page
size, and doesn't require a follow-up rewrite if TASK-007a lands after this ticket starts.
Transitively depends on TASK-004 (`completed`) for the shape of the `GET /config` response.
Independent of TASK-005/TASK-006.

## Acceptance criteria

1. `npm run build` (inside `frontend/`) completes without error and produces a static
   `dist/` bundle.
2. Navigating from `/` to `/settings` and back (via the Settings module card and browser
   back) renders the correct page component each time, verified with React Testing
   Library + a memory router.
3. Every request issued by `api/client.js` carries an `X-API-Key` header whose value
   equals the built `VITE_API_KEY`, verified against a mocked `fetch`.
4. A non-2xx mocked response following the `{"error": {"type", "message"}}` envelope is
   surfaced by `api/client.js` as a JS `ApiError` exposing `type`/`message`/`status`, not
   a raw/unparsed response.
5. Given mocked per-domain responses with different counts for each of the 5 domains, the
   "Ingestions en cours" stat renders the sum across all 5 domains, not a single domain's
   count (proves cross-domain aggregation, not just a single fetch).
6. Same aggregation proof as Criterion 5, independently, for "Propositions en attente".
7. Same aggregation proof as Criterion 5, independently, for "Connaissances canoniques"
   (sum of `ACCEPTED` counts across domains).
8. Given mocked `ACCEPTED`/`REJECTED` proposals with `reviewed_at` timestamps spanning
   more and less than 30 days ago, "Taux d'acceptation" only counts the ones within the
   last 30 days in its ratio; when the resulting denominator is 0, the stat renders "—"
   without a division-by-zero error.
9. The Validation and Ingestion Logs module cards render with a `coming-soon` state and
   are not clickable/navigable; the Settings module card renders `available` and
   navigates to `/settings` when activated.
10. The Dashboard renders a loading state while its 5×N stat requests are in flight, and
    an error state (not a crash) when a mocked request rejects or returns `401`.
11. The Settings screen renders `llm_provider.active`, `default.domain`,
    `retrieval.index_dir`, and `task_state.dir` from a mocked `GET /config` response.
12. The Settings screen contains no editable input, no form submission, and no outgoing
    write/POST/PUT request anywhere in its rendered output or test coverage.
13. The Settings screen's static help text names `~/.pekopeko/config.yaml` (and the
    optional `.env`) and states that editing is manual — present in the rendered output.
14. `frontend/.env.example` contains only placeholder values (e.g. `VITE_API_KEY=changeme`),
    never a real key; `frontend/.gitignore` excludes the real `.env`.
15. `grep -rL` (or equivalent) confirms no component outside `api/client.js` calls the
    global `fetch` directly — every API call is routed through the client wrapper.
16. No file under `src/` is modified by this ticket (`git diff --stat` scoped to `src/`
    is empty once this ticket's changes are isolated).

## Testing requirements

Vitest + React Testing Library, `fetch` fully mocked (`vi.fn()`/`vi.spyOn`, or `msw` if
mocking multiple concurrent domain requests proves cleaner) — no real network calls, no
dependency on a running Flask instance. Minimum cases: one test per acceptance criterion
above (16 total). Project-wide coverage discipline (≥80%) applies to `frontend/src/api/`
and `frontend/src/pages/`.

## Out of scope

- Config write endpoint / editable Settings form — future ticket if the need becomes real
  (superseding the backlog's original "visualise/édite" wording per Cleo's 2026-08-31
  decision).
- Validation, Ingestion Logs, and Proposal Detail screens — TASK-009/TASK-010/TASK-011.
- Domain selector / per-domain Dashboard view.
- Any backend change (aggregate/canonical-count endpoint, or any endpoint at all) — pure
  frontend consuming TASK-007 as already scoped.
- Polling/live updates, WebSocket/SSE.
- TypeScript, global state management library, E2E/browser test tooling.
- Authentication beyond the single shared `X-API-Key` already decided by ADI-010.

## Deviation found and resolved during implementation (2026-09-02)

This ticket's "Taux d'acceptation" spec assumed `GET /domains/<d>/proposals?status=` returns
`reviewed_at` per item. Reading the actual implemented contract
(`src/app/review/pipeline.py`) showed `ProposalSummary` only carries `id, domain,
proposal_status, proposed_item_type, epistemic_status, created_at` — no `reviewed_at`.
That field only exists inside `frontmatter` on the per-item `GET
/domains/<d>/proposals/<id>` detail response. Flagged to Cleo before implementing; resolved
by following TASK-010's existing precedent (N+1 detail fetches) rather than writing a
satellite ticket to extend TASK-007's `ProposalSummary`: for the acceptance-rate stat only,
after fetching `ACCEPTED`/`REJECTED` `ProposalSummary` pages per domain,
`frontend/src/pages/Dashboard.jsx`'s `countRecentlyReviewed` fetches
`GET /domains/<d>/proposals/<id>` for each of those items to read `frontmatter.reviewed_at`
client-side, bounded by TASK-007a's default `limit=50` per domain/status (documented as a
V1 approximation in a code comment, consistent with the ticket's own accepted approximation
for the count-only stats). No backend change; TASK-007/TASK-007a's contracts are untouched.

## Implementation notes

- `frontend/` scaffolded with Vite + React (plain JS/JSX) + React Router 6, exactly per the
  V1 scope decisions above (no TypeScript, no global state library, no E2E tooling).
- `frontend/src/api/client.js` is the single `fetch` wrapper (`get`/`post`), attaching
  `X-API-Key` from `import.meta.env.VITE_API_KEY` and throwing a typed `ApiError`
  (`type`/`message`/`status`) parsed from the `{"error": {...}}` envelope on any non-2xx
  response. Confirmed by grep that no other file under `frontend/src` calls `fetch`
  directly (AC15).
- `frontend/.env.test` (committed, placeholder key only — distinct from the gitignored real
  `frontend/.env`) supplies `VITE_API_KEY`/`VITE_API_BASE_URL` for Vitest's `test` mode, per
  Vite's standard `.env.<mode>` convention.
- Test-environment fix: `@testing-library/react`'s auto-cleanup relies on detecting a global
  `afterEach`; since every test file imports `afterEach` explicitly from `vitest` rather
  than relying on globals, auto-cleanup never registered and DOM from prior tests leaked
  into later ones. Fixed by explicitly calling `afterEach(cleanup)` in
  `frontend/src/test/setup.js`.
- The navigation test (AC2) originally used React Router's `createMemoryRouter` +
  `RouterProvider` (the "data router" API) to test back-navigation, but that crashed in
  jsdom with `TypeError: RequestInit: Expected signal (AbortSignal {}) to be an instance of
  AbortSignal` — a cross-realm bug between jsdom's `AbortController` and Node's
  undici-backed `fetch`/`Request` internals that the data router constructs for its
  fetcher. Worked around by using the plain (non-data) `MemoryRouter`/`Routes` API instead,
  with a test-only `BackButton` component calling `useNavigate(-1)` to drive back
  navigation — avoids the data router entirely, no production code affected.

## Verification record

- `cd frontend && npm install && npm run build` — completes without error, produces
  `dist/index.html` + `dist/assets/*.js` (AC1).
- `npx vitest run` — 13/13 tests pass across `client.test.js` (2), `Dashboard.test.jsx` (8),
  `Settings.test.jsx` (3), one test per acceptance criterion group (AC2-13 covered
  directly; AC1/14/15/16 verified by the manual commands in this section).
- `npx vitest run --coverage` — 96.34% statements/lines, 100% functions, 86.79% branches
  overall on `src/api/` + `src/pages/` (per-file: `client.js` 90.9%, `domains.js` 100%,
  `Dashboard.jsx` 100%, `Settings.jsx` 91.48%) — all above the project's 80% floor
  (`AGENTS.md`).
- `grep -rn "fetch(" frontend/src --include=*.js --include=*.jsx` — only match is
  `frontend/src/api/client.js` (AC15).
- `frontend/.env.example` contains only placeholder values (`VITE_API_KEY=changeme`);
  `frontend/.gitignore` excludes `.env`, `node_modules`, `dist`, `coverage` (AC14).
- `git status --porcelain -- src/` — empty after this ticket's changes (AC16).
- Not independently re-verified by a second reviewer (same limitation as every prior
  ticket in this project) — nor smoke-tested against a real running Flask instance in a
  browser (no local vault/API process available in this session); recommended as a
  follow-up manual check before this screen is relied on operationally.
