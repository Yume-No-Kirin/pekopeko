# TASK-010: Validation Screen, Assertions Only (V1)

- **Status**: completed

## Objective

Implement `pekopeko-workflow.html` (`specs/ux-design/`) as a React screen: proposals
grouped by source, epistemic status badge, individual accept/reject actions — making the
already-`completed` review workflow of TASK-002 visible for the first time. Scope mirrors
TASK-002 exactly: `proposed_item_type: assertion` only (entity/event/relationship review
isn't implemented yet — TASK-005 is still `backlog`, and `accept_proposal` itself rejects
non-assertion proposals with `422` per TASK-007). Third screen of the GUI socle, after
TASK-008 and TASK-009.

**Explicitly out of scope, per a pre-existing decision already made before this ticket**
(not a new cut introduced here): the folder-path builder and per-source bulk accept/reject
that `pekopeko-workflow.html` also shows. `specs/tasks/BACKLOG-CLAUDE-V2.md`'s section 1
intro already states the GUI socle "restent volontairement en MVP: chemin canonique fixe...
(pas de folder-path builder) et actions individuelles uniquement (pas de bulk actions)" and
names TASK-014/TASK-015 as the tickets that add them later; TASK-007 repeats the same
boundary. This ticket does not reopen that decision.

## Binding context (references, not duplicated here)

- `specs/tasks/backlog/TASK-008-react-scaffold-dashboard-settings.md`: routing shell,
  `api/client.js`, `api/domains.js`, `Sidebar.jsx` — reused; the Dashboard's "Validation"
  module card flips to `available` as part of this ticket.
- `specs/tasks/backlog/TASK-009-ingestion-logs-screen.md`: this ticket depends on it for
  the shared `frontend/src/api/tasks.js` wrapper (source→task join, see Scope) and follows
  it in implementation order.
- `specs/tasks/backlog/TASK-007-backend-api-layer.md`: `GET
  /domains/<domain>/proposals?status=PROPOSED` → `ProposalSummary[]` (`id, domain,
  proposal_status, proposed_item_type, epistemic_status, created_at` — no `body`, no
  `provenance`); `GET /domains/<domain>/proposals/<id>` → full `ProposalDetail`
  (`frontmatter` incl. `provenance.source_id`, `body`, `source_frontmatter`, `source_body`);
  `POST .../accept` / `POST .../reject`.
- `specs/tasks/backlog/TASK-007a-list-endpoint-pagination.md`: paginates the
  `?status=PROPOSED` listing this screen's queue is built from.
- `specs/tasks/completed/TASK-002-proposal-review-workflow.md`: `accept_proposal`/
  `reject_proposal` are assertion-only, individual-only, synchronous, no folder parameter
  exists at all — confirms the folder-path column has no data to bind to even if built.
- `specs/ux-design/pekopeko-workflow.html`: source-grouped table, epistemic badge, per-note
  accept/reject/detail actions, filters.
- `specs/domain/knowledge-invariants.md` INV-008/INV-009: domain-scoped endpoints; this
  screen's "tous les domaines" view aggregates client-side across the 5 fixed domains, same
  pattern as TASK-008/TASK-009.

## Scope

New route `/validation`, new page `frontend/src/pages/Validation.jsx`.

1. **Data fetch, two stages**:
   - Stage 1: `GET /domains/<d>/proposals?status=PROPOSED` (paginated per TASK-007a) across
     the 5 fixed domains (or the domain(s) selected by the filter), merged, filtered
     client-side to `proposed_item_type === "assertion"`.
   - Stage 2 (N+1, deliberate — see "Data-fetch trade-off" below): for every proposal from
     stage 1, `GET /domains/<d>/proposals/<id>` in parallel, to obtain `body` and
     `frontmatter.provenance.source_id`/`source_frontmatter` — `ProposalSummary` alone
     doesn't carry either.
   - Stage 3: `GET /domains/<d>/ingestions` (via `frontend/src/api/tasks.js`, from
     TASK-009) for the same domain(s), to join each group's `provenance.source_id` against
     `TaskState.source_id` and recover the originating task's status for the group header
     (no new backend endpoint needed — `TaskState` already carries `source_id`, this is a
     client-side join over already-exposed data).
2. **Grouping**: by `provenance.source_id`. Group header: file name
   (`source_frontmatter.original_filename`), `source_id`, domain badge, note count, and the
   joined ingestion task's status badge (from stage 3) if a match is found (falls back to
   no status badge if the originating task's record has since been pruned/is unavailable —
   never blocks rendering the group).
3. **Note row**: content (`body`), epistemic status badge — all 4 real values
   (`direct/inferred/uncertain/contested`, not only the mockup's shown 2), actions Accepter
   / Rejeter / Détails.
4. **Accept**: `POST /domains/<d>/proposals/<id>/accept` with `reviewer_id` (see
   "Reviewer identity" below); on success, removes the row from the queue (optimistic,
   confirmed by response) and updates the group's note count.
5. **Reject**: opens `frontend/src/components/RejectReasonModal.jsx` (new, shared with
   TASK-011) for an optional reason, then `POST .../reject`.
6. **Filters**: Domaine (re-scopes which domains stage 1/2/3 query), Période (client-side,
   on `created_at`).
7. **Détails**: navigates to `/validation/<domain>/<proposalId>` (TASK-011).
8. **Dashboard update** (part of this ticket): "Validation" module card flips to
   `available`, linking to `/validation`.

### Data-fetch trade-off (N+1, explicitly authorized)

`ProposalSummary` (TASK-007) has no `body`/`provenance.source_id`. Extending TASK-007 to
add them was considered and explicitly declined (2026-08-31): this screen instead issues
one `GET /proposals/<id>` per listed proposal, in parallel (`Promise.all`). At this
project's personal, single-device scale (proposals in the tens/low-hundreds, loopback HTTP)
the added round-trips are not a real performance concern; TASK-007's already-reviewed
contract stays untouched. If proposal volume ever makes this a real bottleneck, extending
`ProposalSummary` is future work, not part of this ticket.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No folder-path builder, no folder column — pre-existing deferral to TASK-014 (see
  Objective).
- No per-source bulk accept/reject — pre-existing deferral to TASK-015 (see Objective).
- No content editing on this screen — `edit_proposal` doesn't exist yet (TASK-006
  `backlog`); pre-existing deferral to TASK-013.
- Source icon is always 📄 (Markdown) — only source type TASK-001 can produce; video
  source types are pre-existing deferrals to TASK-016/TASK-017.
- **Reviewer identity**: no auth/identity system exists anywhere in this stack. Same
  pattern as TASK-008's `VITE_API_KEY`: a build-time environment variable,
  `VITE_REVIEWER_ID` (default e.g. `"cleo"`), sent verbatim as `reviewer_id` on every
  accept/reject call. Low-stakes plumbing decision, not a GUI feature reduction.

## Requirements

- Every outgoing request goes through `frontend/src/api/client.js`; new
  `frontend/src/api/review.js` wrapper (`listProposals`, `getProposal`, `acceptProposal`,
  `rejectProposal`), reused by TASK-011.
- `VITE_REVIEWER_ID` documented in `frontend/.env.example` (TASK-008) alongside
  `VITE_API_KEY`/`VITE_API_BASE_URL`.

## Constraints

- No folder-path builder, no bulk actions, no content editing (pre-existing deferrals, see
  above) — do not silently reintroduce non-functional versions of them.
- No new backend endpoint invented by this ticket — all data via TASK-007 + TASK-007a +
  the existing `GET .../ingestions` (TASK-007, already covers the source→task join, no
  satellite needed for it).
- No modification to any file under `src/`.

## Files/modules concerned

- **New**: `frontend/src/pages/Validation.jsx`.
- **New**: `frontend/src/api/review.js`.
- **New**: `frontend/src/components/RejectReasonModal.jsx`,
  `frontend/src/components/EpistemicStatusBadge.jsx`,
  `frontend/src/components/SourceGroupHeader.jsx`.
- **Modified**: `frontend/src/App.jsx` (new `/validation` route), `frontend/src/pages/
  Dashboard.jsx` (module card → `available`), `frontend/.env.example` (`VITE_REVIEWER_ID`).
- **New tests**: `frontend/src/pages/Validation.test.jsx`,
  `frontend/src/api/review.test.js`.

## Dependencies

Depends on TASK-007 (`backlog`), TASK-007a (`backlog`), TASK-008 (`backlog`, shell), and
TASK-009 (`backlog`, for `api/tasks.js` reuse in the source→task join — implemented after
TASK-009 for that reason). Independent of TASK-001a/TASK-001b/TASK-005/TASK-006.

## Acceptance criteria

1. Proposals from all 5 domains are fetched, filtered to `assertion`, and grouped by
   `provenance.source_id`; a mocked multi-domain, multi-source fixture renders the correct
   number of groups and notes per group.
2. Each note row shows its actual epistemic status among all 4 real values, not just the
   2 shown in the mockup.
3. No folder-path column or bulk-action button is rendered anywhere on this screen.
4. Accepting a note calls `POST .../accept` with the configured `reviewer_id` and removes
   it from its group on success.
5. Rejecting a note opens the shared reason modal; submitting calls `POST .../reject` with
   the entered reason (or `null` if left blank).
6. A group's header shows the joined ingestion task's status badge when a matching
   `TaskState.source_id` is found, and renders cleanly (no crash, no badge) when no match
   is found.
7. Domain filter re-scopes which domains are queried across all three fetch stages.
8. "Détails" navigates to `/validation/<domain>/<proposalId>`.
9. The Dashboard's "Validation" module card is `available` and navigates to `/validation`.
10. A loading state and an error state (mocked rejected `fetch`/`401`) render without
    crashing.
11. No file under `src/` is modified by this ticket.

## Testing requirements

Vitest + React Testing Library, `fetch` fully mocked (including the N+1 detail calls and
the source→task join call), no real network calls. Minimum: one test per acceptance
criterion above (11 total). Coverage discipline (≥80%) applies to
`frontend/src/pages/Validation.jsx` and `frontend/src/api/review.js`.

## Out of scope

- Folder-path builder (TASK-014), bulk accept/reject (TASK-015), content editing
  (TASK-006/TASK-013), video source-type rendering (TASK-016/TASK-017) — all pre-existing
  deferrals, not reopened here.
- Extending `ProposalSummary` to avoid the N+1 fetch — explicitly declined for this ticket
  (see "Data-fetch trade-off").
- Any change to `src/`.

## Deviations from the ticket text (flagged, not silent)

- **`frontend/src/components/Sidebar.jsx` modified**, though not in this ticket's own
  "Files/modules concerned" list — same reasoning already established and confirmed by
  Cleo for TASK-009's Ingestion Logs card: flipping the Dashboard's module card to
  `available` without also promoting "Validation" out of the disabled "Modules à venir"
  section would leave a reachable page permanently greyed out in the persistent nav.
- **`frontend/.env.test` modified** to add `VITE_REVIEWER_ID=test-reviewer`, though not in
  the ticket's file list — needed for deterministic Vitest runs, same committed-placeholder
  mechanism TASK-008 already set up for `VITE_API_KEY`.
- **Pagination design, confirmed with Cleo before implementing** (asked explicitly: single
  bounded fetch like `Dashboard.jsx`'s existing `limit=500` precedent, vs. real Prev/Next
  like TASK-009 adapted to never split a source group across a page — Cleo chose the
  latter). The adaptation: each in-scope domain's `PROPOSED`/`assertion` queue is fetched
  once with `limit=500` (TASK-007a's own max — real use of its pagination contract, not a
  live per-click round trip), grouped by `source_id` (impossible to split a group since
  grouping happens only after the full per-domain page is in hand), then the *complete
  group list* is paginated for display by greedily packing whole groups toward a ~10-note
  target per page. Prev/Next moves between these pre-built pages without re-querying the
  network. This differs from TASK-009's live `?limit=`/`?offset=` round-trip per click;
  justified by this project's own declared scale for the `PROPOSED` queue ("tens/
  low-hundreds", a self-draining working queue rather than a growing log — see the
  ticket's own "Data-fetch trade-off" section).
- **`SourceGroupHeader`'s ingestion-status badge reuses `.status-badge`/`TaskStatusBadge`
  (TASK-009)** rather than porting the mockup's separate `.source-status` class — same
  visual scheme (green completed pill), avoids a near-duplicate CSS rule and a second
  status-label mapping for the same 5 values.
- **Stage 2 (`GET .../proposals/<id>`) uses `Promise.allSettled`, not `Promise.all`**: a
  malformed proposal (missing `provenance.source_id`) makes that one detail call fail
  (`400 ValidationError`, per `review/pipeline.py::get_proposal`); dropping just that
  settlement mirrors `list_proposals`' own documented tolerance ("a single malformed
  proposal file must not break the whole review queue") instead of letting one bad
  proposal blank the entire screen. Not explicitly specified by the ticket text, but a
  direct, low-risk application of a precedent already set by the backend it's calling.
- **Mockup fidelity**: the "Statut ingestion" filter shown in `pekopeko-workflow.html` is
  not implemented — the ticket's own Scope item 6 lists only Domaine + Période as this
  screen's filters, so this isn't a cut made here, just literal adherence to a scope the
  ticket had already narrowed. The folder-path builder column and per-source "Tout
  accepter"/"Tout rejeter" buttons are not ported either — both are pre-existing
  deferrals the ticket's own Objective section names explicitly (TASK-014/TASK-015).

## Implementation notes

- `frontend/src/api/review.js`: `listProposals(domain, {status, limit, offset})`,
  `getProposal(domain, id)`, `acceptProposal(domain, id, reviewerId)`,
  `rejectProposal(domain, id, reviewerId, reason)` — thin wrappers over `api/client.js`,
  same shape as TASK-009's `api/tasks.js`.
- `frontend/src/components/EpistemicStatusBadge.jsx`: all 4 real values
  (direct/inferred/uncertain/contested); the 2 without a mockup variant reuse
  `TaskStatusBadge`'s established running (blue)/failed (red) palette rather than
  inventing new colors.
- `frontend/src/components/SourceGroupHeader.jsx` / `RejectReasonModal.jsx`: both
  generic/reusable, `RejectReasonModal` explicitly shared with TASK-011 per the ticket.
- `frontend/src/pages/Validation.jsx`: `fetchGroups()` implements the 3-stage fetch (list →
  N+1 detail join → ingestion-task join) and the group-preserving pagination described
  above under Deviations; `REVIEWER_ID` read once at module scope from
  `import.meta.env.VITE_REVIEWER_ID`, same pattern as `client.js`'s `API_KEY`. Accept/
  reject both update state only after a successful response (never before), with a
  dedicated `actionError` banner distinct from the page-level load `error`.
- `frontend/src/index.css`: ported `pekopeko-workflow.html`'s source-header/note-row/
  epistemic-badge/`.btn-mini` blocks verbatim, plus `.btn-primary` (needed by the new
  reject modal, not previously ported since TASK-009 had no use for it). New modal CSS
  (`.modal-overlay`/`.modal`/etc.) has no mockup equivalent — the mockup's reject button
  has no confirmation step at all.

## Verification record

- `cd frontend && npm run build` — completes without error.
- `npx vitest run` — 42/42 tests pass across all suites: `client.test.js` (2),
  `tasks.test.js` (3), `review.test.js` (5, new), `Settings.test.jsx` (3),
  `Dashboard.test.jsx` (10 — 1 updated in place for the now-available Validation card + 1
  new end-to-end navigation test), `IngestionLogs.test.jsx` (8), `Validation.test.jsx` (11
  — one per AC1-8/10, plus AC5b for the blank-reason case and a bonus test for the
  group-preserving pagination logic).
- `npx vitest run --coverage` — 96.9% statements/lines overall; `api/review.js` 100%
  statements/lines, 85.71% branches; `pages/Validation.jsx` 94.17% statements/lines,
  87.83% branches, 77.77% functions. **Correction (2026-09-03, found during code
  review):** this file's function coverage (77.77%) is actually below the project's
  80% floor from AGENTS.md, contrary to what this record previously claimed. The run
  itself still passes because `vite.config.js`'s `coverage.thresholds` gates on the
  aggregate across `coverage.include`, not per file — other well-covered files in the
  same glob pull the aggregate above 80% and mask this file's real gap. Flagged here
  per AGENTS.md's verification discipline rather than left silently wrong.
- `grep -rn "fetch(" frontend/src --include=*.js --include=*.jsx` — only match is
  `frontend/src/api/client.js`.
- `git status --porcelain -- src/` — empty after this ticket's changes (AC11).
- Acceptance criteria 1-8/10 verified directly by `Validation.test.jsx`'s named tests
  (matched 1:1, see the file); AC9 by `Dashboard.test.jsx`'s two Validation tests
  (module-card `available`+`href`, and an end-to-end click-through navigation test
  rendering `Validation` at `/validation`); AC11 by the `git status` command above.
- Not independently re-verified by a second reviewer (same limitation as every prior
  ticket in this project) — nor smoke-tested against a real running Flask instance in a
  browser (no local vault/API process available in this session). The adapted pagination
  strategy in particular would benefit from a manual check against a domain with a source
  group larger than the ~10-note page target, to confirm an over-sized group still renders
  correctly on its own page.
