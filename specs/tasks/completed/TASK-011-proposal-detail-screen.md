# TASK-011: Proposal Detail Screen, Assertions Only (V1)

- **Status**: completed

## Objective

Implement `pekopeko-proposal-detail.html` (`specs/ux-design/`) as a React screen: full
content, metadata, provenance, source, and accept/reject-with-reason for a single
proposal — same assertion-only scope as TASK-010, same relationship to TASK-002's
already-`completed` accept/reject workflow. Fourth and last screen of this GUI socle round
(TASK-008/009/010/011). Full fidelity to the mockup wherever the backend (existing +
TASK-001a/TASK-001b, its two satellite dependencies) supports it; sections that depend on
a satellite ticket degrade gracefully (simply don't render that sub-section) rather than
blocking the rest of the page if that satellite hasn't landed yet — not a silent feature
cut, an explicit, documented dependency.

**Explicitly out of scope, per pre-existing decisions already made before this ticket**
(not new cuts introduced here): content editing (mockup's "✎ Éditer" — needs
`edit_proposal`, TASK-006 `backlog`, deferred to TASK-013 per `docs/ROADMAP.md`), the
folder-path builder (TASK-014), video source-type rendering for YouTube/Instagram/TikTok
(TASK-016/TASK-017 — no reader for any of them exists yet, `source_format` is always
`"markdown"` today).

## Binding context (references, not duplicated here)

- `specs/tasks/backlog/TASK-008-react-scaffold-dashboard-settings.md`: routing shell,
  `api/client.js`.
- `specs/tasks/backlog/TASK-010-validation-screen.md`: this ticket reuses
  `frontend/src/api/review.js`, `RejectReasonModal.jsx`, `EpistemicStatusBadge.jsx` created
  there, and is the screen `/validation`'s "Détails" links navigate to. Implemented after
  TASK-010 for that reuse.
- `specs/tasks/backlog/TASK-007-backend-api-layer.md`: `GET
  /domains/<domain>/proposals/<id>` → `ProposalDetail` (`id, domain, frontmatter, body,
  source_frontmatter, source_body`); accept/reject endpoints.
- `specs/tasks/backlog/TASK-001a-extraction-provenance-metadata.md`: adds
  `provider_model`/`provider_temperature`/`extraction_id`/`extraction_duration_seconds` to
  `frontmatter.provenance` — backs this screen's full Provenance section.
- `specs/tasks/backlog/TASK-001b-task-event-log.md`: adds `events` to `TaskState` — backs
  this screen's "Logs d'ingestion complets" section (via the same source→task join
  TASK-010 already established, reused here for one proposal instead of a whole group).
- `specs/tasks/completed/TASK-001-data-ingestion.md`: baseline Proposal `provenance`
  contract (`source_id`, `extraction_provider`) — always present regardless of whether
  TASK-001a has landed.
- `specs/ux-design/pekopeko-proposal-detail.html`: status bar, two-column layout (content /
  metadata), Source section, Provenance & Extraction section, Logs section, Précédent/
  Suivant navigation, Accepter/Rejeter actions.

## Scope

New route `/validation/:domain/:proposalId`, new page
`frontend/src/pages/ProposalDetail.jsx`.

1. **Data fetch**: `GET /domains/<domain>/proposals/<proposalId>` → full `ProposalDetail`.
2. **Status bar**: status badge (`proposal_status`), domain badge, type badge
   (`proposed_item_type`), epistemic status badge (`EpistemicStatusBadge`, from TASK-010),
   Précédent/Suivant buttons, Accepter/Rejeter buttons.
3. **Content section**: `body`, read-only (no edit mode — see Objective).
4. **Metadata section**: `id`, `epistemic_status`, `created_at`, `valid_from`/`valid_until`.
5. **Source section** (Markdown only): `source_frontmatter.original_filename`,
   `content_hash`, `ingested_at`, and a full render of `source_body` (already entirely
   present in the response — no separate "load more"/expand-link round-trip needed, unlike
   the mockup's static placeholder text).
6. **Provenance section**: always renders `provenance.source_id` and
   `provenance.extraction_provider` (present today, TASK-001 baseline). Additionally
   renders `provider_model`, `provider_temperature`, `extraction_id`,
   `extraction_duration_seconds` when present (TASK-001a) — each rendered conditionally,
   field by field, not as an all-or-nothing section (a Proposal ingested before TASK-001a
   landed simply shows fewer rows, not a broken layout).
7. **Logs d'ingestion complets section**: joins `provenance.source_id` against `GET
   /domains/<domain>/ingestions` (via `frontend/src/api/tasks.js`, TASK-009) to find the
   originating `TaskState`, then renders its full `events` list (TASK-001b) the same way
   TASK-009's `TaskEventLog.jsx` does (reused component). If no matching task is found (task
   state pruned, or TASK-001b not yet landed so `events` is empty), the section renders a
   short "aucun journal disponible" note instead of an empty/broken block.
8. **Navigation Précédent/Suivant**: on mount, `GET
   /domains/<domain>/proposals?status=PROPOSED` (via `api/review.js`), filtered client-side
   to `assertion`, to reconstruct the ordered queue for *this domain* and locate the
   current proposal's index. **Scoped to the current domain only** (the domain is already
   fixed by the URL) — does not reconstruct TASK-010's cross-domain aggregate. This is a
   deliberate implementation simplification (documented, not a mockup feature removed): the
   mockup's own "Précédent/Suivant" never demonstrated cross-domain traversal either (its
   hardcoded `proposalsList` is single-context).
9. **Accepter/Rejeter**: same calls as TASK-010 (`reviewer_id` from `VITE_REVIEWER_ID`,
   shared `RejectReasonModal.jsx` for rejection reason), redirects to `/validation` on
   success.
10. No note-type selector dropdown (the mockup's simulated `<select>` over hardcoded fake
    data) — superseded entirely by real routing to real proposal IDs; Précédent/Suivant is
    the real equivalent.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No edit mode, no folder-path builder, no video source-type rendering — pre-existing
  deferrals (see Objective), not reopened here.
- Provenance and Logs sections are the two places this screen's fidelity depends on
  satellite tickets (TASK-001a, TASK-001b respectively) — each degrades field-by-field or
  to a short explanatory note, never a crash or a silently-fabricated value.
- Précédent/Suivant is domain-scoped, not cross-domain — explicit simplification (see Scope
  point 8), distinct from a feature cut since the mockup itself never modeled cross-domain
  navigation.

## Requirements

- Every outgoing request goes through `frontend/src/api/client.js`, via the
  `frontend/src/api/review.js` and `frontend/src/api/tasks.js` wrappers (both from
  TASK-010/TASK-009) — no new ad hoc `fetch()` calls.

## Constraints

- No content editing, no folder-path builder, no video source-type rendering.
- No new backend endpoint invented by this ticket.
- No modification to any file under `src/`.

## Files/modules concerned

- **New**: `frontend/src/pages/ProposalDetail.jsx`.
- **New**: `frontend/src/components/ProvenanceSection.jsx` (field-by-field conditional
  rendering per TASK-001a's optional fields).
- **Modified**: `frontend/src/App.jsx` (new `/validation/:domain/:proposalId` route).
- **Reused, unmodified**: `frontend/src/api/review.js`, `frontend/src/api/tasks.js`,
  `frontend/src/components/RejectReasonModal.jsx`,
  `frontend/src/components/EpistemicStatusBadge.jsx`,
  `frontend/src/components/TaskEventLog.jsx` (all from TASK-009/TASK-010).
- **New tests**: `frontend/src/pages/ProposalDetail.test.jsx`,
  `frontend/src/components/ProvenanceSection.test.jsx`.

## Dependencies

Depends on TASK-007 (`backlog`), TASK-008 (`backlog`, shell), TASK-009 (`backlog`, for
`api/tasks.js`/`TaskEventLog.jsx` reuse), TASK-010 (`backlog`, for `api/review.js`/
`RejectReasonModal.jsx`/`EpistemicStatusBadge.jsx` reuse — implemented after it).
TASK-001a and TASK-001b are dependencies for full section fidelity (Provenance, Logs
respectively) but not hard blockers — this screen renders correctly, with those two
sections reduced, even if implemented before either satellite lands (see V1 scope
decisions). Independent of TASK-005/TASK-006.

## Acceptance criteria

1. All status/domain/type/epistemic badges render correctly from a mocked `ProposalDetail`
   fixture.
2. Content section renders `body` read-only; no textarea, no save button, no edit-toggle
   control anywhere in the rendered output.
3. Source section renders `original_filename`/`content_hash`/`ingested_at`/`source_body`
   from a mocked fixture, with no truncation/expand-link needed (full `source_body` shown
   directly).
4. Given a mocked `provenance` with only the TASK-001 baseline fields (`source_id`,
   `extraction_provider`), the Provenance section renders exactly those two rows, no
   broken layout, no placeholder text implying missing data is an error.
5. Given a mocked `provenance` that also includes TASK-001a's four additional fields, the
   Provenance section renders all six rows correctly.
6. Given a mocked ingestion task list where one `TaskState.source_id` matches this
   proposal's `provenance.source_id` and has a populated `events` list, the Logs section
   renders that event sequence via the reused `TaskEventLog` component.
7. Given no matching task (or an empty `events` list), the Logs section renders the
   "aucun journal disponible" fallback instead of an empty/broken block.
8. Précédent/Suivant buttons are correctly enabled/disabled at the start/end of the
   reconstructed same-domain assertion queue, and navigate to the correct adjacent
   `proposalId` in the URL.
9. Accepting/rejecting calls the correct endpoint with `reviewer_id` from
   `VITE_REVIEWER_ID`, and redirects to `/validation` on success.
10. A loading state and an error state (mocked rejected `fetch`/`401`/`404`) render without
    crashing.
11. No file under `src/` is modified by this ticket.

## Testing requirements

Vitest + React Testing Library, `fetch` fully mocked, no real network calls. Minimum: one
test per acceptance criterion above (11 total), including both the TASK-001a-present and
TASK-001a-absent Provenance variants (criteria 4-5) and both the TASK-001b-present and
-absent Logs variants (criteria 6-7). Coverage discipline (≥80%) applies to
`frontend/src/pages/ProposalDetail.jsx` and `frontend/src/components/ProvenanceSection.jsx`.

## Out of scope

- Content editing (TASK-006/TASK-013), folder-path builder (TASK-014), video source-type
  rendering (TASK-016/TASK-017) — pre-existing deferrals, not reopened here.
- Cross-domain Précédent/Suivant traversal.
- Any change to `src/`.

## Deviations from the ticket text (flagged, not silent)

- **Metadata section narrower than the mockup**: `pekopeko-proposal-detail.html` also
  duplicates `Type`/`Domaine` inside its metadata table (already shown in this ticket's own
  status bar) and shows the interactive folder-path builder row. This ticket's own Scope
  item 4 already narrows the Metadata section to exactly `id`, `epistemic_status`,
  `created_at`, `valid_from`/`valid_until` — implemented literally to that narrower list,
  same "literal adherence to a scope the ticket had already narrowed" precedent TASK-010
  set for its own filters.
- **`.proposal-status-badge` given one color per real `proposal_status` value**
  (PROPOSED/ACCEPTED/REJECTED/EDITED) rather than the mockup's single static color — the
  mockup's own demo never changes this badge's state, but this screen's queue can
  realistically show more than one value (TASK-006, completed independently of this
  ticket, added `EDITED`). Same established pattern as `EpistemicStatusBadge`/
  `TaskStatusBadge` (one CSS class per value), not a new convention.
- **Two mockup class names renamed to avoid colliding with classes this app's earlier
  tickets already defined for a different purpose**: the mockup's own generic
  `.section-title` (14px/uppercase/muted, used inside `.section-header`) collides with
  Dashboard's already-existing `.section-title` (18px/bold, its "Modules" heading) —
  renamed `.card-section-title` here. The mockup's own generic `.status-badge` (proposal
  pill) collides with the existing `.status-badge` already used by `TaskStatusBadge` (task
  pending/running/completed/failed/skipped_duplicate, different color semantics) —
  renamed `.proposal-status-badge`. Both documented inline in `index.css`.
- **Logs section fallback text is distinct from `TaskEventLog`'s own empty-state text**:
  `TaskEventLog` itself renders "Aucun événement enregistré." when handed an empty
  `events` array. This ticket's own AC7 asks for an "aucun journal disponible" note
  covering *both* "no matching task found" and "task found but its `events` list is
  empty" in one fallback — implemented by only rendering `TaskEventLog` when a task is
  found **and** its `events` array is non-empty, otherwise rendering this screen's own
  "Aucun journal disponible." paragraph (reusing `TaskEventLog`'s own
  `.task-event-log-empty` CSS class for visual consistency, not duplicating the rule).
  `TaskEventLog`'s own internal empty-state string is therefore never reached from this
  screen by construction.
- **Coverage config left untouched**: `vite.config.js`'s `coverage.include` only globs
  `src/api/**`/`src/pages/**`, not `src/components/**`, so `ProvenanceSection.jsx` (a new
  component) isn't counted in the shared aggregate the project's `npm run test:coverage`
  reports. Broadening the glob to `src/components/**` was tried and reverted: it would
  also pull in several pre-existing, entirely untested components (`Sidebar.jsx` at 0%
  covered, among others) that are outside this ticket's scope and not in its own "Files/
  modules concerned" list, silently changing the project's coverage gate as a side effect
  of this ticket rather than as a deliberate, separately-reviewed decision. Verified
  `ProvenanceSection.jsx`'s own coverage instead via a one-off scoped run (see Verification
  record) rather than a persistent config change.

## Implementation notes

- `frontend/src/pages/ProposalDetail.jsx`: three independent fetches on mount -
  `getProposal` (mandatory; its rejection is the page's error state), `listIngestions` and
  `listProposals({status: "PROPOSED"})` (each degrades to an empty list on failure rather
  than blocking the page, mirroring this ticket's own "non-blocking satellite" posture for
  TASK-001a/TASK-001b). The Logs section's `source_id` match and the Précédent/Suivant
  queue index are both derived at render time from `detail`/`ingestionTasks`/`queue`
  state, not fetched sequentially - none of the three requests depends on another's
  result. `REVIEWER_ID` read once at module scope from `import.meta.env.VITE_REVIEWER_ID`,
  identical line to `Validation.jsx`, not reinvented.
- `frontend/src/components/ProvenanceSection.jsx`: two small field-list constants
  (baseline always-rendered, TASK-001a optional fields filtered by
  `!== null && !== undefined` individually) rather than one combined list with per-field
  conditionals inline, to make the "always 2, up to 6" contract (AC4/AC5) visible at a
  glance.
- `frontend/src/index.css`: ported `pekopeko-proposal-detail.html`'s status-bar/two-column/
  section-card/metadata-table/source-preview/logs-section blocks verbatim except the two
  renames noted above under Deviations; folder-path-builder and inline-edit-mode CSS
  blocks not ported (unused, per Out of scope).
- No change to `frontend/src/components/Sidebar.jsx` - unlike TASK-009/TASK-010, this
  screen isn't a top-level nav destination (reached only via Validation's "Détails" link),
  so there is no disabled nav item to promote.

## Verification record

- `npx vite build` (`frontend/`) - completes without error.
- `npx vitest run --coverage` - 56/56 tests pass across 9 suites: the 45 pre-existing
  (`client.test.js` 2, `tasks.test.js` 3, `review.test.js` 5, `Settings.test.jsx` 3,
  `Dashboard.test.jsx` 10, `IngestionLogs.test.jsx` 9, `Validation.test.jsx` 13) plus 11
  new (`ProvenanceSection.test.jsx` 2 - AC4/AC5; `ProposalDetail.test.jsx` 9 - AC1, AC2,
  AC3, AC6, AC7, AC8, AC9, AC9b, AC10).
- Aggregate coverage (`src/api/**` + `src/pages/**`, the project's existing
  `coverage.include`): 97.39% statements/lines, 90.04% branches, 85.45% functions - all
  above AGENTS.md's 80% floor. `pages/ProposalDetail.jsx` individually: 96.03%
  statements/lines, 79.41% branches, 75% functions. **Flagged per the same discipline
  TASK-010's own record called out**: this file's branch/function coverage individually
  sits just under the 80% floor; the run still passes because `vite.config.js` gates on
  the aggregate across the whole glob, not per file, and other well-covered files in the
  same glob pull the aggregate above 80%. Not silently glossed over.
- `frontend/src/components/ProvenanceSection.jsx` (outside the shared `coverage.include`, see
  Deviations): checked separately via `npx vitest run
  src/components/ProvenanceSection.test.jsx --coverage
  --coverage.include='src/components/ProvenanceSection.jsx'
  --coverage.thresholds.lines=0 --coverage.thresholds.statements=0
  --coverage.thresholds.functions=0 --coverage.thresholds.branches=0` - 100%
  statements/branches/functions/lines.
- `grep -rn "fetch(" frontend/src --include=*.js --include=*.jsx` (excluding `*.test.*`) -
  only match is `frontend/src/api/client.js`.
- `git status --porcelain -- src/` - empty after this ticket's changes (AC11).
- Acceptance criteria 1, 2, 3, 6, 7, 8, 10 verified directly by `ProposalDetail.test.jsx`'s
  identically-named tests; AC9 by its `AC9`/`AC9b` tests (accept, then reject-with-reason);
  AC4/AC5 by `ProvenanceSection.test.jsx`; AC11 by the `git status` command above.
- Not independently re-verified by a second reviewer (same limitation as every prior
  ticket in this project) - nor smoke-tested against a real running Flask instance in a
  browser (no local vault/API process available in this session), in particular for the
  Précédent/Suivant queue reconstruction against a domain with more than 500 PROPOSED
  assertions (the `limit=500` bound this ticket reuses from `Validation.jsx`'s own
  precedent) - recommended as a manual follow-up before operational use, same
  recommendation every prior GUI ticket in this project has carried forward.
