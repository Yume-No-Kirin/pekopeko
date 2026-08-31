# TASK-010: Validation Screen, Assertions Only (V1)

- **Status**: backlog

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
names TASK-013/TASK-015 as the tickets that add them later; TASK-007 repeats the same
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

- No folder-path builder, no folder column — pre-existing deferral to TASK-013 (see
  Objective).
- No per-source bulk accept/reject — pre-existing deferral to TASK-015 (see Objective).
- No content editing on this screen — `edit_proposal` doesn't exist yet (TASK-006
  `backlog`); pre-existing deferral to TASK-014.
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

- Folder-path builder (TASK-013), bulk accept/reject (TASK-015), content editing
  (TASK-006/TASK-014), video source-type rendering (TASK-016/TASK-017) — all pre-existing
  deferrals, not reopened here.
- Extending `ProposalSummary` to avoid the N+1 fetch — explicitly declined for this ticket
  (see "Data-fetch trade-off").
- Any change to `src/`.
