# TASK-011: Proposal Detail Screen, Assertions Only (V1)

- **Status**: backlog

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
`edit_proposal`, TASK-006 `backlog`, deferred to TASK-014 per `docs/ROADMAP.md`), the
folder-path builder (TASK-013), video source-type rendering for YouTube/Instagram/TikTok
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

- Content editing (TASK-006/TASK-014), folder-path builder (TASK-013), video source-type
  rendering (TASK-016/TASK-017) — pre-existing deferrals, not reopened here.
- Cross-domain Précédent/Suivant traversal.
- Any change to `src/`.
