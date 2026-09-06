# TASK-015: Review Queue Bulk Operations and Filter/Sort (V1)

- **Status**: backlog

## Objective

Add per-source-group bulk accept/reject to `Validation.jsx` — mirroring
`pekopeko-workflow.html`'s "Tout accepter"/"Tout rejeter" buttons, present in the maquette but
explicitly deferred by TASK-010's own MVP scope ("no per-source bulk accept/reject — pre-existing
deferral to TASK-015") — plus filter/sort controls beyond the existing Domaine/Période: a
proposition-type filter, an epistemic-status filter, and a sort-order control. This is the first
entry of `specs/tasks/BACKLOG-CLAUDE-V2.md`'s section 2 (re-prioritization proposal, not yet an
acted decision as a whole) to be extracted into a full ticket, following TASK-013/TASK-014.

Scope now covers all 4 `proposed_item_type` values (assertion/entity/event/relationship): TASK-012
(entity/event/relationship review — API integration + GUI), closing that gap, is `completed` as of
this same session (see `docs/ROADMAP.md`'s TASK-012 section for the status-desync correction made
alongside this ticket) — `Validation.jsx` already fetches, groups, and renders all 4 types.

## Binding context (references, not duplicated here)

- `specs/ux-design/pekopeko-workflow.html`: the maquette this ticket ports the bulk-action part
  of — `.source-actions` cell with `.btn-small.accept-all`/`.btn-small.reject-all` per
  `source-header-row`, calling (in the static mockup) `acceptAllFromSource(sourceId)`/
  `rejectAllFromSource(sourceId)`. The maquette's own "Statut ingestion" filter is **not** part of
  this ticket (TASK-010 already scoped that out explicitly; not reopened here).
- `specs/tasks/completed/TASK-010-validation-screen.md`: names TASK-015 as the ticket that adds
  "per-source bulk accept/reject" and "bulk actions (accept/reject all)" — this ticket's entire
  reason to exist. Its "Data-fetch trade-off" section (N+1 detail fetch per proposal) is unchanged
  by this ticket: bulk actions operate on already-fetched, already-grouped `groups` state.
- `specs/tasks/completed/TASK-012-entity-event-relationship-review-gui.md`: closed the
  assertion-only gap this ticket would otherwise have inherited — `Validation.jsx` already has no
  `proposed_item_type` filter of its own (TASK-012 removed it), so this ticket's new type filter is
  additive UI, not a lift of an existing restriction.
- `frontend/src/pages/Validation.jsx` (current code, read in full while writing this ticket):
  `fetchGroups()` (fetches `PROPOSED`+`EDITED` across domains, joins per-proposal detail via
  `Promise.allSettled`, groups by `provenance.source_id`), `visibleGroups` (current filter
  pipeline: period only, via `filterByPeriod` from `frontend/src/utils/periodFilter.js`),
  `packGroupsIntoPages`/`NOTES_PER_PAGE` (pagination, unaffected by this ticket), `rejectTarget`
  state + `RejectReasonModal` (currently single-`id` only), `updateGroupsAfterRemoval` (currently
  single-`id` only).
- `frontend/src/components/SourceGroupHeader.jsx` (current code): renders one `<td
  colSpan={columnCount}>` covering the whole row — no action cell exists today. Its own comment
  ("No accept-all/reject-all here - bulk actions are a pre-existing deferral (TASK-015), not a cut
  made by this screen") is the exact deferral this ticket closes.
- `src/app/review/pipeline.py::accept_proposal`/`reject_proposal` (current code, read in full):
  single-`proposal_id`, synchronous, atomic-write-per-item, **no auto-cascade** — a relationship
  proposal whose `endpoints` include an id matching another proposal that isn't yet `ACCEPTED`
  raises `UnresolvedRelationshipEndpointError` (TASK-005's own explicit V1 decision, unchanged and
  not reopened here). This ticket's batch endpoints do not retry, reorder, or auto-accept
  dependencies — a batch simply reports that item as failed, same semantics as calling `/accept`
  on it individually would.
- `src/app/api/routes_review.py`/`serialization.py`/`app.py`'s `ERROR_STATUS_MAP` (current code,
  read in full): existing `/accept`/`/reject`/`/edit` routes and their error-mapping table — this
  ticket adds two new routes to the same blueprint, reusing `review.pipeline.accept_proposal`/
  `reject_proposal` verbatim, and does **not** touch `ERROR_STATUS_MAP` or `review/` itself.
- INV-001 (Universal Human Validation): a batch accept is still N individual proposals a human
  explicitly asked to accept via one click on a visible, already-rendered group — not a new
  auto-approval path or a relaxation of per-item review.
- `specs/domain/knowledge-invariants.md` has no invariant specific to bulk operations; the
  relevant constraint is TASK-005's own no-auto-cascade decision, reused as-is (see above).

## Scope

### Backend (new)

1. `POST /domains/<domain>/proposals/accept-batch` — body `{"reviewer_id": str, "proposal_ids":
   [str, ...]}`. For each `proposal_id`, **in the given order**, calls the existing
   `review.pipeline.accept_proposal(vault_root, domain, proposal_id, reviewer_id)` unchanged.
2. `POST /domains/<domain>/proposals/reject-batch` — body `{"reviewer_id": str, "proposal_ids":
   [str, ...], "reason": str | null}`. Same loop, calling the existing
   `review.pipeline.reject_proposal(vault_root, domain, proposal_id, reviewer_id, reason=reason)`
   — the **same** `reason` (or `None`) is passed for every id in the batch (per Cleo's scoping
   decision: one optional reason for the whole group, not per-item).
3. Both routes live only in `src/app/api/routes_review.py` — **no change to `src/app/review/`**.
   Each item's call is wrapped in a `try`/`except review.errors.ReviewError` (the shared base
   class already defined in `review/errors.py`): a failure for one `proposal_id` is recorded as a
   per-item error entry and processing continues with the next id — **the batch never aborts and
   the HTTP response is always `200`** for a structurally valid request (same "a single bad item
   must not break the whole operation" precedent already established by `list_proposals`).
4. Response envelope (both routes, via a new shared serializer):
   `{"results": [{"proposal_id": str, "status": "accepted"|"rejected"|"failed", "error":
   {"type": str, "message": str} | null, ...fields from AcceptResult/RejectResult when
   successful}, ...], "succeeded_count": int, "failed_count": int}`. `results` preserves the
   input order of `proposal_ids`.
5. A structurally invalid request — missing/blank `reviewer_id`, `proposal_ids` missing, not a
   list, or an empty list — raises the existing `review.errors.ValidationError` (→ `400`, already
   mapped) **before** any item is processed. This is the route's own validation, not a change to
   `review/`.
6. No new exception class, no change to `ERROR_STATUS_MAP` in `src/app/api/app.py` — per-item
   failures are captured and serialized inline, never re-raised to Flask's error handler.

### Frontend

7. `frontend/src/components/SourceGroupHeader.jsx` gains a second `<td>` (action cell,
   `colSpan` on the info cell reduced from `columnCount` to `columnCount - 1`) with "✓ Tout
   accepter" / "✕ Tout rejeter" buttons, mirroring the maquette's `.btn-small.accept-all`/
   `.reject-all` classes (already ported into `index.css` per TASK-010's implementation notes,
   confirm still present/reuse as-is). New props: `onAcceptAll(domain, ids)`,
   `onRejectAll(domain, ids)`.
8. **Bulk actions act only on the notes currently visible for that group after all active
   filters** (Domaine/Période/the two new filters below) — not on notes hidden by a filter. Since
   `Validation.jsx` already builds `visibleGroups` by filtering each group's `notes` array before
   rendering, `group.notes` as received by `SourceGroupHeader` in the current page is already the
   correct post-filter set; the action handlers read `group.notes.map(n => n.id)` from that same
   prop, no separate "all ids" list needed.
9. "Tout accepter" has no confirmation step (mirrors individual accept's own lack of
   confirmation) and immediately calls the new `acceptProposalsBatch(domain, ids, reviewerId)`
   wrapper.
10. "Tout rejeter" opens the existing `RejectReasonModal` **once** for the whole group (not once
    per note). `Validation.jsx`'s existing `rejectTarget` state (currently `{domain, id}` for a
    single note) needs a second, parallel target shape for a batch — e.g. a
    `rejectTarget = {domain, ids}` (an array, `ids: [id]` for the existing individual-reject path,
    or the group's full visible id list for bulk) that both `handleRejectClick` and the new
    `handleRejectAllClick` populate, with `handleRejectConfirm` dispatching to
    `rejectProposalsBatch` for both cases — this generalizes the existing single-reject path onto
    the same new batch endpoint rather than keeping two separate reject code paths. **Individual
    accept keeps calling the existing single `/accept` endpoint unchanged** (no equivalent
    generalization pressure there — accept has no shared modal to unify).
11. On a batch response: notes whose per-item `status` is not `"failed"` are removed from state
    (extends the existing `updateGroupsAfterRemoval` to accept multiple ids at once); notes whose
    `status === "failed"` stay in the queue, and their errors are surfaced in a dedicated banner
    (extends the existing `actionError` pattern to list one message per failed item, e.g. "3/5
    notes acceptées, 2 échouées : <id> — Endpoint(s) [...] are not yet ACCEPTED proposals" ), never
    silently dropped.
12. Two new filters added to `Validation.jsx`'s `.filters-bar`, both **client-side** (all 4 types
    and every note's `epistemic_status` are already present in the already-fetched `groups`
    state — no backend change needed):
    - **Type de proposition**: Tous / Assertion / Entity / Event / Relationship — filters on
      `note.detail.frontmatter.proposed_item_type`.
    - **Statut épistémique**: Tous / Direct / Inféré / Incertain / Contesté — filters on
      `note.epistemic_status`, reusing the same 4 values/labels as `EpistemicStatusBadge`.
    Both compose with the existing Domaine/Période filters and with each other (a note must pass
    all active filters to remain visible) — same `visibleGroups` pipeline, extended with two more
    predicates alongside the existing `filterByPeriod` call.
13. One new **sort order** control (client-side, no backend change — grouping/pagination already
    happen entirely client-side after fetch): "Plus récent d'abord" (default, matches TASK-007a's
    existing most-recent-first convention) / "Plus ancien d'abord". Sorts `visibleGroups` by each
    group's most recent note's `created_at` before `packGroupsIntoPages` runs.
14. New `frontend/src/api/review.js` wrappers: `acceptProposalsBatch(domain, ids, reviewerId)` →
    `POST /domains/${domain}/proposals/accept-batch`; `rejectProposalsBatch(domain, ids,
    reviewerId, reason)` → `POST /domains/${domain}/proposals/reject-batch` — same thin-wrapper
    style as the existing `acceptProposal`/`rejectProposal` in that file.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **No arbitrary multi-select** (checkboxes across or within a group) — bulk actions apply to a
  whole source group's currently-visible notes only, exactly as the maquette shows. A future
  ticket, not this one, would add free selection if ever needed.
- **One shared optional reason for a bulk reject**, not one modal per note (Cleo's explicit
  choice) — a bulk reject that needs per-item nuance still requires falling back to individual
  rejects.
- **New dedicated batch endpoints**, not a frontend loop over the existing single-item
  `/accept`/`/reject` routes (Cleo's explicit choice) — keeps the per-item error handling and the
  "always 200 with a results array" contract on the backend rather than reimplemented in
  `Validation.jsx`.
- **No auto-cascade / no reordering within a batch** — same decision TASK-005/TASK-012 already
  made for the single-item case, simply inherited: a relationship near the front of a batch whose
  endpoint is later in the same batch (or not in the batch at all) fails with
  `UnresolvedRelationshipEndpointError`, exactly as an individual accept would; the reviewer can
  always accept the endpoint first and retry the rest, same workflow as today.
- **Individual accept/reject actions are left calling the existing single-item endpoints
  unchanged** — only the new group-level buttons use the batch endpoints (except reject's shared
  modal, item 10 above, which generalizes onto the batch endpoint with a 1-item list for the
  individual case, since it already shares one modal/handler). This minimizes the blast radius on
  already-shipped, already-tested code paths.
- No new canonical-item read endpoint, no change to `review/`'s per-item contract, no change to
  `ERROR_STATUS_MAP` — same minimal-surface posture as TASK-012.
- The maquette's "Statut ingestion" filter remains out of scope, same as TASK-010's own decision —
  not reopened here.

## Requirements

- **Backend**: Python only (ADI-007), Flask (ADI-010) — no new dependency. The two new routes are
  orchestration only (loop + per-item try/except + serialize), no new business logic file.
- **Frontend**: React function components, existing `api/client.js`/`api/review.js` wrappers, no
  new frontend dependency.

## Constraints

- No file under `src/app/review/` is modified by this ticket.
- No change to `ERROR_STATUS_MAP` or any existing exception class in `src/app/api/`.
- No change to the response shape or behavior of the existing single-item `/accept`, `/reject`,
  `/edit` routes.
- No arbitrary multi-select, no per-item bulk-reject reason, no auto-cascade — see V1 scope
  decisions above.

## Files/modules concerned

- **Backend** (new): 2 routes in `src/app/api/routes_review.py`; 1 new serializer (e.g.
  `batch_response`) in `src/app/api/serialization.py`.
- **Backend** (new tests): `src/tests/api/test_review_routes.py` additions (or a new
  `test_review_batch_routes.py`, matching this project's existing file-granularity conventions).
- **Frontend** (modified in place): `frontend/src/pages/Validation.jsx` (filters, sort, bulk
  handlers, generalized reject-target state), `frontend/src/components/SourceGroupHeader.jsx`
  (action cell + buttons), `frontend/src/api/review.js` (2 new wrappers).
- **Frontend** (new/updated tests): `frontend/src/api/review.test.js`,
  `frontend/src/components/SourceGroupHeader.test.jsx` (new — this component currently has no
  test file), `frontend/src/pages/Validation.test.jsx` (extended with bulk/filter/sort fixtures).
- No file under `src/app/review/` or `src/app/extraction/` is touched.

## Dependencies

- TASK-007/TASK-007a (`completed`) — the API layer and pagination this ticket's routes extend.
- TASK-010 (`completed`) — `Validation.jsx`/`SourceGroupHeader.jsx`, extended in place.
- TASK-012 (`completed`, this same session) — removed the `assertion`-only filter, so this
  ticket's scope legitimately covers all 4 `proposed_item_type` values from the start.
- Independent of TASK-006/TASK-013/TASK-014 (edit mode, folder-path builder) — no interaction
  with either; a note being edited or mid folder-path-edit is unaffected by this ticket's filters/
  sort/bulk actions.

## Acceptance criteria

1. "Tout accepter" on a group with N currently-visible notes issues exactly one
   `accept-batch` call with all N ids (and no others); when every item succeeds, the whole
   group disappears from the queue.
2. A batch containing one relationship proposal whose endpoint isn't yet `ACCEPTED` returns
   `succeeded_count < proposal_ids.length` and `failed_count >= 1`; that item's `error.type ==
   "UnresolvedRelationshipEndpointError"`; the corresponding note stays visible in its group
   afterward, and the other, successful items in the same batch are removed.
3. "Tout rejeter" opens exactly one `RejectReasonModal` for the group (not one per note);
   confirming issues one `reject-batch` call carrying every visible id in the group and the
   single entered (or blank → `null`) reason.
4. The Type de proposition filter, set to a single type, hides notes of every other type from
   both the on-screen list and from the id list any bulk action for that group would use;
   setting it back to "Tous" restores them.
5. The Statut épistémique filter behaves identically to AC4 for `epistemic_status`, and composes
   correctly with the Type filter and with the existing Domaine/Période filters (a fixture with
   notes matching some but not all active filters renders only the fully-matching notes).
6. The sort-order control reorders groups by their most recent note's `created_at`, both
   directions, verified against a fixture with known, distinct timestamps across at least 3
   groups.
7. A fixture where some notes of a group are filtered out (by any of the 4 filters) confirms
   those notes' ids are excluded from that group's next bulk `accept-batch`/`reject-batch` call.
8. `accept-batch`/`reject-batch` return HTTP `200` for any request containing at least one valid
   `proposal_id`, even when every item in it fails — only a structurally invalid request (missing
   `reviewer_id`, missing/non-list/empty `proposal_ids`) returns `400`.
9. Individual accept/reject (single note, existing UI) still call the pre-existing single-item
   `/accept`/`/reject` endpoints unchanged — a regression test confirms no individual action was
   silently rerouted to the new batch endpoints (except the shared reject modal, which is
   confirmed instead to send a 1-item `proposal_ids` array to `reject-batch` for the individual
   case, per item 10's design).
10. No file under `src/app/review/` is modified by this ticket (`git status --porcelain --
    src/app/review/` empty after implementation).

## Testing requirements

- **Backend**: `pytest`, Flask `app.test_client()`, `tmp_path` fixtures with a mix of
  assertion/entity/event/relationship proposals (including at least one relationship with an
  unresolved endpoint) to exercise partial-failure batches. Minimum: one test per acceptance
  criterion 1-2/8/10 above (backend-observable ones), plus explicit all-succeed and all-fail batch
  cases.
- **Frontend**: same mocked-`fetch`/React Testing Library pattern as `Validation.test.jsx`
  (TASK-010), extended with fixtures covering AC1, AC3-AC7, AC9; no real network calls. Coverage
  discipline (≥80%, AGENTS.md) applies to every file this ticket touches or adds.

## Out of scope

- Arbitrary checkbox multi-select across or within groups.
- A new canonical entity/event/relationship read endpoint.
- Auto-cascade or reordering of items within a batch (a relationship's endpoint dependency is
  never auto-resolved).
- Any change to `review/pipeline.py`'s single-item `accept_proposal`/`reject_proposal` contract,
  or to `ERROR_STATUS_MAP`.
- Per-item bulk-reject reasons (one shared reason per batch only).
- The maquette's "Statut ingestion" filter (pre-existing TASK-010 deferral, not reopened).
- Folder-path bulk edit (distinct from accept/reject; not addressed here).
