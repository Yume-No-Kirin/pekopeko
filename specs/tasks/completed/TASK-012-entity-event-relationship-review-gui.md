# TASK-012: Entity, Event and Relationship Review — API Integration and GUI (V1)

- **Status**: completed

## Objective

Close the assertion-only gap left open by the GUI socle (TASK-007 → TASK-011): entity, event, and
relationship proposals can already be listed/fetched generically by TASK-007's API
(`ProposalSummary`/`ProposalDetail` carry no type restriction), but `accept_proposal`/
`reject_proposal` still reject them (`UnsupportedProposalTypeError`, TASK-007 AC10) because TASK-005
— the ticket that teaches `review/` to accept/reject these 3 types — is written but not yet
implemented, and both `Validation.jsx` (TASK-010) and `ProposalDetail.jsx` (TASK-011) hard-filter
their queues to `proposed_item_type === "assertion"` for the same reason.

This ticket has two independent implementation halves (Python, React) closing the same visualization
gap, which is why `specs/tasks/BACKLOG-CLAUDE-V2.md` groups them under one ticket:

- **Backend**: implement TASK-005 exactly as already written, plus the two small integration points
  TASK-005 itself leaves open because it predates the API layer (naming its new error class; mapping
  it to an HTTP status in `src/app/api/`).
- **Frontend**: extend `Validation.jsx`/`ProposalDetail.jsx` to stop filtering out entity/event/
  relationship proposals, and add rendering for their type-specific fields (`entity_type`;
  `starts_at`/`ends_at`; `relationship_type` + `endpoints`).

Once both halves land, TASK-003's extraction output (`completed`) is visualizable/reviewable
end-to-end for all 4 proposal types, and TASK-007's AC10 (422 for non-assertion accept) is
superseded — see Scope/Backend below.

## Binding context (references, not duplicated here)

- **TASK-005** (`specs/tasks/backlog/TASK-005-entity-event-relationship-review.md`, `backlog`,
  already fully written): this ticket's *entire* backend scope, unchanged. Read that ticket directly
  for its objective, file contract, endpoint-resolution rules, and 10 acceptance criteria — not
  reproduced here. This ticket only adds the 2 integration points TASK-005 leaves unnamed (see
  Scope/Backend).
- **TASK-003** (`specs/tasks/completed/TASK-003-entity-event-relationship-extraction.md`,
  `completed`): the Proposal frontmatter contract this ticket's frontend renders —
  `entity_type` (entity only), `starts_at`/`ends_at` (event only), `relationship_type` + `endpoints`
  (relationship only) — already present verbatim in `ProposalDetail.frontmatter` today, no backend
  change needed to read it.
- **TASK-007** (`specs/tasks/backlog/TASK-007-backend-api-layer.md`, `backlog`): its
  `GET /domains/<d>/proposals[/<id>]` endpoints are already type-agnostic (no `proposed_item_type`
  filter exists at the API level — the restriction is entirely inside `accept_proposal`); its error
  mapping table (`src/app/api/app.py`) is what this ticket extends; its AC10 is what this ticket
  supersedes.
- **TASK-010**/**TASK-011** (`backlog`): `Validation.jsx`/`ProposalDetail.jsx`, the two client-side
  `proposed_item_type === "assertion"` filters this ticket removes, and the existing
  `EpistemicStatusBadge`/`RejectReasonModal`/`api/review.js` this ticket reuses unchanged.
- **ADI-003** (relationship-model, Accepted): canonical relationships reference stable ids, never
  duplicated content, and traversal is a derived, non-canonical adjacency structure (future
  TASK-020) — backs this ticket's decision to resolve endpoint labels only from data already
  fetched for other reasons, rather than adding a new canonical-item-by-id read endpoint.
- `specs/domain/knowledge-invariants.md`: INV-001/INV-003/INV-008 — already cited by TASK-005 for
  the backend half, not re-justified here. INV-011 (representations are not canonical truth):
  the frontend half is a projection of the same review queue TASK-005 operates on; it introduces no
  new persistence, only new rendering.
- `specs/ux-design/README.md`: confirms (and this ticket notes explicitly, see V1 scope decisions)
  that neither `pekopeko-workflow.html` nor `pekopeko-proposal-detail.html` models entity_type,
  temporal bounds, or relationship endpoints — there is no maquette to port for this ticket's new UI.

## Scope

### Backend

1. Implement TASK-005 exactly as written — no change to its scope, file contract, or 10 acceptance
   criteria. Its own file lists the modules to change (`review/storage.py`, `review/pipeline.py`,
   `review/errors.py`) and is the authoritative spec for that work.
2. Name TASK-005's unnamed "typed error for unresolved (not-yet-accepted) relationship endpoints"
   `UnresolvedRelationshipEndpointError`, defined in `review/errors.py` alongside `review/`'s other
   typed exceptions.
3. Extend TASK-007's error-mapping table/handler (`src/app/api/app.py`) with one new row:
   `UnresolvedRelationshipEndpointError` (module `review.errors`) → HTTP `409` — same status as
   `InvalidProposalStatusError`, for the same reason: the request is well-formed but a state
   precondition (the endpoint's own proposal must already be `ACCEPTED`) isn't met yet.
4. TASK-007's Acceptance Criterion 10 ("`POST .../accept` on an entity/event/relationship proposal
   returns 422 ... TASK-005 not yet landed") is **superseded** once TASK-005 and this ticket are both
   implemented: acceptance now succeeds normally for entity/event/relationship proposals (subject to
   endpoint resolution, point 3 above). `UnsupportedProposalTypeError`/422 fires only for a genuinely
   unrecognized `proposed_item_type` from that point on, per TASK-005 Scope item 5.

### Frontend

5. `frontend/src/pages/Validation.jsx` — remove the `proposed_item_type === "assertion"`
   client-side filter (TASK-010, Scope item 1). All 4 types are fetched, detail-fetched (N+1, as
   today), and grouped by `provenance.source_id` unchanged — only the type filter is lifted.
6. `frontend/src/pages/ProposalDetail.jsx` — remove the equivalent filter in the Précédent/Suivant
   queue reconstruction (TASK-011, Scope item 8): the same-domain queue now includes all 4 types.
7. Add 3 new presentational components, reused by both pages, following the existing badge
   conventions (`EpistemicStatusBadge.jsx`, the mockups' `.domain-badge`/`.epistemic-badge` classes):
   - `frontend/src/components/EntityTypeBadge.jsx` — renders `entity_type`.
   - `frontend/src/components/EventTemporalRange.jsx` — renders `starts_at`/`ends_at`; each is
     independently nullable and must render a "non précisé" placeholder rather than break layout.
   - `frontend/src/components/RelationshipEndpoints.jsx` — renders `relationship_type` and the
     `endpoints` list. Purely presentational: takes already-resolved `{id, label: string | null}[]`
     as a prop; resolving labels is the calling page's responsibility (point 8).
8. Endpoint label resolution — no new backend endpoint (TASK-007 exposes no canonical-item-by-id
   read, and adding one is out of scope, see V1 scope decisions):
   - **`Validation.jsx`**: reuse the existing N+1 `ProposalDetail` fetch (already run per listed
     proposal, now covering all 4 types per point 5) as a `Map<proposal_id, ProposalDetail>`. An
     endpoint id present in that map resolves to a label (its `proposed_item_type` plus a short
     `body` excerpt); an id absent from the map renders as a plain, unlabeled identifier
     (already-canonical passthrough, or a proposal outside the current `PROPOSED` view).
   - **`ProposalDetail.jsx`**: no batch is already in memory (single-proposal page), so each
     relationship's `endpoints` triggers one targeted `getProposal(domain, endpointId)` call — an
     explicit N+1 trade-off in the same category TASK-010 already established, not a new API
     surface. A `404` response is caught and treated as "id already canonical" (plain identifier, no
     label), consistent with TASK-005's own backend simplification for the same case.
   - Both call sites de-duplicate ids already resolved or already in flight, so a chain of
     relationships referencing each other cannot trigger redundant or repeated requests.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **No maquette exists for this ticket's new UI.** Per `specs/ux-design/README.md`, both
  `pekopeko-workflow.html` and `pekopeko-proposal-detail.html` model only the assertion/note review
  flow — `entity_type`, temporal bounds, and relationship endpoints have no established visual
  precedent anywhere in the corpus. The 3 new components (point 7) reuse only the existing badge
  visual convention, not a specific layout; this is new UI design, not a maquette port.
- **No new backend read endpoint for canonical items.** Endpoint labels are best-effort from data
  the two pages already fetch for other reasons (point 8); an unresolvable id renders as a plain
  identifier rather than blocking the page or growing the API surface. Revisit only as its own future
  ticket if this proves insufficient once TASK-020 (adjacency/traversal) exists.
- **`UnresolvedRelationshipEndpointError` → `409`** is this ticket's own decision, not inherited from
  an existing ADR — TASK-005 predates the API layer and leaves both the class name and HTTP status
  open. If a different status is preferred (e.g. `422`, matching `UnsupportedProposalTypeError`'s
  "well-formed but not currently actionable" semantics), that is a one-line change to the mapping
  table, not a design change.
- **No auto-cascade / no bulk accept from the frontend either**, matching TASK-005's own backend
  decision: a relationship whose endpoint isn't yet accepted still requires the reviewer to navigate
  to and accept that endpoint first. The resulting `409` surfaces through the existing generic
  error-state handling already built by TASK-010/TASK-011 (their AC10/AC10-equivalent loading/error
  states) — no new error UI is introduced by this ticket.
- Same MVP boundary as the rest of the GUI socle: no folder-path builder (TASK-014), no bulk actions
  (TASK-015), no content editing (TASK-006/TASK-013).

## Requirements

- **Backend**: identical to TASK-005 (Python/`pyyaml` only, atomic writes, validate-before-write),
  plus: the new `UnresolvedRelationshipEndpointError` is added to `src/app/api/app.py`'s existing
  error-mapping table/handler — not a parallel or duplicate mapping mechanism.
- **Frontend**: identical to TASK-010/TASK-011 (React function components, existing `api/client.js`/
  `api/review.js` wrappers, no new frontend dependency), plus: the two new client-side fetch sites
  (point 8) reuse `api/review.js`'s existing `getProposal` — no new API wrapper function.

## Constraints

- Same as TASK-005: no `EDITED` status, no bulk ops, no `history/`, no database, no validation of
  non-proposal endpoint ids against disk, no dependency on `app.extraction`, no cross-domain review,
  no auth beyond the existing `X-API-Key`.
- No file under `src/app/review/` beyond what TASK-005 itself specifies — this ticket's only backend
  addition outside `review/` is the single error-mapping entry in `src/app/api/app.py`.
- No file under `src/` is modified by the frontend half — same boundary TASK-010/TASK-011 already
  hold themselves to.

## Files/modules concerned

- **Backend** (= TASK-005's own list, by reference): `src/app/review/storage.py`,
  `src/app/review/pipeline.py`, `src/app/review/errors.py`, `src/tests/review/`.
- **Backend** (new, this ticket only): `src/app/api/app.py` (one new error-mapping row/handler
  branch), `src/tests/api/` (one new test asserting the `409` mapping, one updated test for the
  superseded AC10).
- **Frontend** (modified in place): `frontend/src/pages/Validation.jsx`,
  `frontend/src/pages/ProposalDetail.jsx`.
- **Frontend** (new): `frontend/src/components/EntityTypeBadge.jsx`,
  `frontend/src/components/EventTemporalRange.jsx`,
  `frontend/src/components/RelationshipEndpoints.jsx`, plus a `*.test.jsx` for each, and updated
  fixtures in `Validation.test.jsx`/`ProposalDetail.test.jsx` covering mixed-type data.

## Dependencies

- **Backend**: TASK-005 (`backlog`, unchanged — this ticket's backend scope in full) and TASK-007
  (`backlog` — the error-mapping table extended here, and the AC10 superseded here). Implementable
  only once both exist in the codebase.
- **Frontend**: TASK-008 → TASK-009 → TASK-010 → TASK-011 (`backlog`, existing chain — edits pages
  and reuses components those tickets create). Independent of TASK-006/TASK-014/TASK-015 (all
  separately deferred).

## Acceptance criteria

Backend — TASK-005's own 10 criteria apply unchanged (see that ticket for full text; not renumbered
or reproduced here), plus:

11. `UnresolvedRelationshipEndpointError` (as raised by TASK-005's `accept_proposal`) maps to HTTP
    `409` with `error.type == "UnresolvedRelationshipEndpointError"` via `src/app/api/app.py`'s
    error handler, verified by a Flask `test_client()` test in `src/tests/api/`.
12. `POST .../accept` on an entity/event/relationship proposal whose endpoints (if any) are already
    resolvable now returns `200` — superseding TASK-007's AC10 — verified by updating that test in
    `src/tests/api/` to assert the new success path instead of the old `422`.

Frontend:

13. A mocked multi-type fixture (assertion + entity + event + relationship proposals across at least
    2 sources) renders on `Validation.jsx` with correct per-source grouping and one row per
    proposal — none filtered out by type.
14. Each entity row/detail shows its `entity_type` via `EntityTypeBadge`; each event row/detail shows
    `starts_at`/`ends_at` via `EventTemporalRange`, including a fixture where one of the two is
    `null`, rendering without crashing.
15. Each relationship row/detail shows its `relationship_type` and resolved `endpoints` via
    `RelationshipEndpoints` — one fixture case where an endpoint id matches another proposal already
    fetched (label shown), one where `getProposal` mocks a `404` for that id (plain id shown, no
    crash).
16. `ProposalDetail.jsx`'s Précédent/Suivant queue, built from a mocked same-domain fixture mixing
    all 4 types, correctly enables/disables its buttons and navigates across every type, not just
    assertions.
17. Accepting/rejecting an entity/event/relationship proposal from either screen calls the existing
    `acceptProposal`/`rejectProposal` wrapper unchanged; a mocked `409
    UnresolvedRelationshipEndpointError` response renders through the screens' existing generic
    error-state handling (no new UI branch) with the backend's message visible to the reviewer.
18. A fixture where two relationship proposals reference each other's `proposal_id` as an endpoint
    does not trigger duplicate or repeated fetches for the same id (the mocked `getProposal`/fetch is
    called at most once per unique id).
19. No folder-path column and no bulk-action control appear anywhere on either screen after this
    ticket.
20. No file under `src/` is modified by the frontend half of this ticket.

## Testing requirements

- **Backend**: `pytest`, extends TASK-005's own test plan (see that ticket) with one Flask
  `test_client()` case for AC11 and an updated case for TASK-007's former AC10 (now AC12) — both
  under `src/tests/api/`.
- **Frontend**: same mocked-fetch/React Testing Library pattern as `Validation.test.jsx`/
  `ProposalDetail.test.jsx` (TASK-010/TASK-011), extended with mixed-type fixtures per AC13-AC18
  above; no real network calls.

## Out of scope

- Everything TASK-005 already scopes out: `EDITED`/`history/`, non-proposal endpoint disk
  validation, auto-cascade/bulk acceptance, adjacency/traversal structure (TASK-020).
- Folder-path builder (TASK-014), bulk actions (TASK-015), content editing (TASK-006/TASK-013) —
  same GUI-socle boundary as TASK-010/TASK-011.
- Any new backend endpoint for reading a canonical entity/event/relationship by id — endpoint labels
  are best-effort from already-fetched proposal data only (see V1 scope decisions).
- A dedicated graph/traversal view of accepted relationships — TASK-020, once the adjacency structure
  (ADI-003) exists.
- Any change to `ProposalSummary`/`ProposalDetail`'s JSON shape — both already carry every field this
  ticket needs.

## Verification record

Implemented 2026-09-06 (commit `7b0e794`, "TASKS 005 et 012, event, entity, relations"), together
with TASK-005. **Documentation gap found and corrected 2026-09-06, in a later session**: this
ticket's own file was left `backlog` and `docs/ROADMAP.md` kept citing it as the sole remaining
GUI-socle ticket/next action, despite the code already being on `main` — a real desync between
"État actuel" and repo reality (the exact failure mode AGENTS.md's continuity discipline warns
about), not a new implementation gap. No dedicated Verification record was written at
implementation time; the check below was run retroactively, in the same session that fixed the
status desync, not independently of the implementation.

- `[PASS]` Backend — `pytest src/tests/review src/tests/api` (from repo root): 253/253 pass.
  `--cov=src.app.review --cov=src.app.api`: 99% combined (`routes_review.py`/`pipeline.py`/
  `storage.py`/`errors.py` all 100%; the only misses are pre-existing, unrelated to this ticket —
  `app.py` lines 68/99-100/104, generic-exception fallback branches, and `tasks.py` 18-19).
- `[PASS]` AC11 (`UnresolvedRelationshipEndpointError` → `409`) and AC12 (accept succeeds for
  entity/event/relationship, superseding TASK-007's old AC10) — covered by
  `src/tests/api/test_error_mapping.py` and `test_review_routes.py` (both updated in the same
  commit), included in the 253 passing above.
- `[PASS]` Frontend — `npx vitest run` (from `frontend/`): 13 test files, 100/100 pass, including
  `EntityTypeBadge.test.jsx`, `EventTemporalRange.test.jsx`, `RelationshipEndpoints.test.jsx`
  (AC13-15), and mixed-type fixtures inside `Validation.test.jsx`/`ProposalDetail.test.jsx`
  (AC16-18). `npx vitest run --coverage`: 98.45% lines overall; `Validation.jsx` 97.8%,
  `ProposalDetail.jsx` 98.97% lines, though `ProposalDetail.jsx`'s function coverage (68.75%)
  sits below the project's 80% floor in isolation — same aggregate-masks-a-per-file-gap pattern
  already flagged for `Validation.jsx` in TASK-010's own Verification record, not a new issue.
  `src/components/*.test.jsx` files pass but sit outside `vite.config.js`'s coverage `include`
  glob (pre-existing scope, already noted in TASK-011).
- `[PASS]` Regression — `src/tests/extraction` (72/72), `src/tests/config` (39/39),
  `src/tests/acceptance` (21/21, excluding `e2e`) all pass run independently per-folder.
  `src/tests/ingestion` 96/98 pass, with the same 2 pre-existing, unrelated failures
  (`test_acceptance_criteria_compliance`, `test_import_isolation`) documented repeatedly in
  `docs/ROADMAP.md` for prior tickets. Running all of `src/tests/` in one invocation still hits
  the pre-existing, already-documented collection collision on duplicate `test_storage.py`/
  `_helpers.py` module names without `__init__.py` — unrelated to this ticket, worked around by
  testing each subfolder separately, same as prior sessions.
- `[NOT RUN]` No dedicated manual end-to-end reproduction against a live Flask instance/real
  vault was performed as part of this retroactive check (none was available in this session,
  same limitation already recorded for TASK-010/TASK-011). Not independently reviewed by a
  second reviewer — same limitation as every other ticket in this project.
