# TASK-013: Proposal Edit Mode — API Endpoint and Frontend (V1)

- **Status**: backlog

## Objective

Make `review.edit_proposal` (TASK-006, `completed`) usable end-to-end. TASK-006 implemented the
full backend mechanism — `PROPOSED`/`EDITED` → `EDITED`, the `history/` versioning snapshot, the
`EDITABLE_FIELDS_BY_TYPE` allow-list — but TASK-007 (the HTTP API layer, `completed`) explicitly
left it unreachable over HTTP: *"No edit endpoint: `review.edit_proposal` does not exist yet
(TASK-006 not implemented) — out of scope here ... edit is TASK-013, once TASK-006 lands"*
(`specs/tasks/completed/TASK-007-backend-api-layer.md`). TASK-006 has since landed, so that gap is
now the actionable part of this ticket, not a re-implementation of TASK-006 itself.

Per `specs/tasks/BACKLOG-CLAUDE-V2.md`'s TASK-013 entry: *"Backend: implémente TASK-006 tel qu'il
est déjà rédigé ... Frontend: ajoute un mode édition dans l'écran Détail (TASK-011/012) — champs
éditables selon l'allow-list de TASK-006, bouton de sauvegarde appelant edit_proposal."* Read
literally, "backend: implement TASK-006" is misleading now that TASK-006 is `completed` — the real
backend work here is exposing the already-implemented function as a route, following TASK-007's
own `/accept`/`/reject` conventions.

This ticket scopes its frontend half to `ProposalDetail.jsx` (TASK-011) only, **not** waiting on
TASK-012 (Entity/Event/Relationship GUI integration, still `backlog`) — same posture TASK-011
itself already used to ship without TASK-012. `edit_proposal` is type-generic in the backend (see
Binding context), so nothing here blocks TASK-012 from reusing the same endpoint later; the
frontend UI stays assertion-scoped only because `ProposalDetail.jsx`/`Validation.jsx` themselves
still filter to `proposed_item_type === "assertion"` today.

**Numbering note**: `TASK-011`'s and `TASK-012`'s ticket text (both written 2026-08-31, the same
day as `BACKLOG-CLAUDE-V2.md`) originally cited "TASK-014" for this work and "TASK-013" for the
folder-path builder — the reverse of `BACKLOG-CLAUDE-V2.md`'s current numbering. Cleo confirmed
`BACKLOG-CLAUDE-V2.md` is authoritative (2026-09-04); the swapped references in
`TASK-007-backend-api-layer.md`, `TASK-011-proposal-detail-screen.md`,
`TASK-012-entity-event-relationship-review-gui.md`, and `docs/ROADMAP.md` were corrected in the
same session this ticket was written. The folder-path builder is TASK-014.

## Binding context (references, not duplicated here)

- **TASK-006** (`specs/tasks/completed/TASK-006-proposal-edit-and-history.md`, `completed`): full
  spec of the mechanism this ticket exposes. Its `edit_proposal(vault_root, domain, proposal_id,
  reviewer_id, body=None, field_updates=None) -> EditResult` (`src/app/review/pipeline.py:160-201`)
  is **not modified** by this ticket — called exactly as-is.
  `EDITABLE_FIELDS_BY_TYPE["assertion"] = {"body", "epistemic_status", "valid_from",
  "valid_until"}` (`src/app/review/storage.py:42-49`) is the allow-list this ticket's frontend form
  must match field-for-field, no more.
- **TASK-007** (`specs/tasks/completed/TASK-007-backend-api-layer.md`, `completed`): the
  `/accept`/`/reject` route conventions this ticket's new route must follow exactly
  (`src/app/api/routes_review.py:42-58`) — `_check_domain`, `request.get_json(silent=True) or {}`,
  `jsonify(...), 200` — and the `ERROR_STATUS_MAP`/`register_error_handler` mechanism in
  `src/app/api/app.py:32-45,82-83` this ticket adds one row to.
- **TASK-010**/**TASK-011** (`completed`): `Validation.jsx` and `ProposalDetail.jsx`, the pages
  this ticket edits; `RejectReasonModal.jsx` (`frontend/src/components/RejectReasonModal.jsx`) as
  the existing pattern for a controlled draft-state UI with Confirmer/Annuler actions; `api/review.js`
  as the wrapper module this ticket extends.
- `specs/ux-design/pekopeko-proposal-detail.html` (lines ~723-741, ~1398-1442 in the mockup file):
  the "✎ Éditer" toggle / textarea / Sauvegarder / Annuler pattern for the content field — the only
  part of this ticket's UI with an existing visual precedent. The mockup's `saveEdit()` is
  client-side only (`contentDisplay.textContent = textarea.value`, no persistence); this ticket
  wires the same visual pattern to the real endpoint. Per `specs/ux-design/README.md`, the mockup
  does **not** model editing any metadata field (`epistemic_status`, `valid_from`, `valid_until`)
  or an `EDITED` status color — both are net-new UI this ticket must design, not port.
  `pekopeko-workflow.html` (Validation screen mockup) has no edit affordance at all — confirmed
  read-only by design in its own README section and row markup.
- `frontend/src/pages/ProposalDetail.jsx:12-17`: `PROPOSAL_STATUS_LABELS` already includes
  `EDITED: "Éditée"`, and `frontend/src/index.css:906-909` already defines
  `.proposal-status-badge.EDITED` (comment at `index.css:833-838` names it explicitly as part of
  the original 4-status set) — added proactively by TASK-011. **No new status-badge work is
  needed**; this ticket only needs to confirm the existing badge renders correctly once a real
  `EDITED` proposal exists.
- ADI-001 (canonical-persistence-model, Accepted): the `history/` snapshot behavior this ticket
  surfaces is already backed by this ADR via TASK-006 — no new persistence decision here.

## Scope

### Backend

1. New route in `src/app/api/routes_review.py`:
   `POST /domains/<domain>/proposals/<proposal_id>/edit`, registered on the existing `review_bp`
   (no new blueprint). Body: `{"reviewer_id": "<str>", "body": "<str, optional>",
   "field_updates": {"epistemic_status": "<str>", "valid_from": "<str|null>",
   "valid_until": "<str|null>"}, optional}`. Handler:
   ```python
   @review_bp.route("/domains/<domain>/proposals/<proposal_id>/edit", methods=["POST"])
   def edit(domain, proposal_id):
       _check_domain(domain)
       body = request.get_json(silent=True) or {}
       reviewer_id = body.get("reviewer_id")
       result = edit_proposal(
           _vault_root(), domain, proposal_id, reviewer_id,
           body=body.get("body"), field_updates=body.get("field_updates"),
       )
       return jsonify(serialization.edit_result_to_dict(result)), 200
   ```
   (`edit_proposal` imported alongside the module's existing `accept_proposal`/`get_proposal`/
   `list_proposals`/`reject_proposal` import.)
2. New `serialization.edit_result_to_dict(result)` in `src/app/api/serialization.py`, same pattern
   as `accept_result_to_dict` (`serialization.py:117-120`) since `EditResult.archived_version_path`
   is a `Path`:
   ```python
   def edit_result_to_dict(result) -> Dict[str, Any]:
       data = asdict(result)
       data["archived_version_path"] = str(result.archived_version_path)
       return data
   ```
3. `src/app/api/app.py`: import `UneditableFieldError` alongside the other `review.errors` imports
   (`app.py:17-22`) and add `UneditableFieldError: 400` to `ERROR_STATUS_MAP` (`app.py:32-45`) —
   currently unmapped, so it would fall through to the generic 500 handler today. No other error
   needs a new mapping: `InvalidProposalStatusError` (409, `app.py:42`) already covers
   accept/reject/**edit** per its own docstring; `DomainMismatchError` (400) and the generic
   `ReviewValidationError` (400, covers both missing `reviewer_id` and the "both body and
   field_updates empty" case) are already mapped and reachable through this new route unchanged.
4. No change to `src/app/review/` — `edit_proposal` is called exactly as TASK-006 left it. No
   change to `ProposalDetail`'s JSON shape (an editor refetches via the existing
   `GET /domains/<domain>/proposals/<proposal_id>` to see the new `body`/frontmatter after a save,
   same pattern already used after accept/reject navigation).

### Frontend

5. `frontend/src/api/review.js`: new `editProposal(domain, id, reviewerId, { body, fieldUpdates })`
   following the existing `acceptProposal`/`rejectProposal` shape:
   ```js
   export function editProposal(domain, id, reviewerId, { body, fieldUpdates } = {}) {
     return post(`/domains/${domain}/proposals/${id}/edit`, {
       reviewer_id: reviewerId,
       body: body ?? null,
       field_updates: fieldUpdates ?? null,
     });
   }
   ```
6. `frontend/src/pages/ProposalDetail.jsx`: single "✎ Éditer" toggle button in the status-bar
   `.action-buttons` area, shown whenever Accepter/Rejeter are (i.e. `frontmatter.proposal_status`
   is `PROPOSED` or `EDITED`). Entering edit mode seeds four local draft fields from `detail`:
   `body`, `epistemic_status`, `valid_from`, `valid_until`. While editing:
   - Content card ("Contenu de la proposition") swaps its read-only `.content-display` for a
     `<textarea>` bound to the draft `body` — same visual pattern as the mockup's `#contentTextarea`.
   - Metadata card ("Métadonnées") swaps its `epistemic_status` row for a `<select>` populated from
     `EpistemicStatusBadge`'s own 4-value label set (`direct`/`inferred`/`uncertain`/`contested`,
     `frontend/src/components/EpistemicStatusBadge.jsx:1-6`), and its `valid_from`/`valid_until`
     row for two text inputs. `ID Proposition` and `Créé le` stay read-only (not in the allow-list).
   - The status-bar's Rejeter/Accepter/✎Éditer trio is replaced by Sauvegarder/Annuler (mirrors
     `RejectReasonModal`'s Confirmer/Annuler pair) — accepting/rejecting mid-edit is not offered;
     the reviewer must save or cancel first.
   - Sauvegarder calls `editProposal(domain, proposalId, REVIEWER_ID, { body: draftBody,
     fieldUpdates: { epistemic_status: draftEpistemicStatus, valid_from: draftValidFrom || null,
     valid_until: draftValidUntil || null } })`; on success, refetches `getProposal(domain,
     proposalId)` to refresh `detail` (new `body`, `proposal_status: "EDITED"`, etc.) and exits
     edit mode. On failure, surfaces the error through the existing `actionError` banner
     (`ProposalDetail.jsx:157-161`) and **stays in edit mode** with the draft intact.
   - Annuler discards the draft and returns to read-only display without calling the API.
7. `frontend/src/pages/Validation.jsx` (`fetchGroups`, line 26) and
   `frontend/src/pages/ProposalDetail.jsx` (queue-building effect, line 69) currently fetch only
   `listProposals(domain, { status: "PROPOSED", ... })`. **Fix required**: once a proposal can
   become `EDITED`, it would otherwise silently disappear from both the Validation queue and the
   Précédent/Suivant navigation, even though `accept_proposal`/`reject_proposal` already accept it
   (TASK-006). `list_proposals`'s `status` filter is single-value exact-match only
   (`review/pipeline.py:79`, no multi-value support) — fix by fetching `status: "PROPOSED"` and
   `status: "EDITED"` per domain in parallel (`Promise.all`, same fan-out style already used for
   the existing multi-domain calls) and merging the two result sets before the existing
   grouping/filtering logic runs.
8. `frontend/src/index.css`: add edit-mode classes. TASK-011 explicitly did not port the mockup's
   `.editable-content`/`.content-edit`/`.content-textarea`/`.edit-actions`/`.btn-small` blocks
   ("unused, per Out of scope" at the time — `TASK-011`'s Implementation notes) — this ticket needs
   them now, plus new classes for the metadata `<select>`/text inputs (no mockup precedent, since
   the mockup never modeled metadata editing). No change needed to `.proposal-status-badge.EDITED`
   (already exists, see Binding context).

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **Frontend stays assertion-only**, matching `Validation.jsx`/`ProposalDetail.jsx`'s own current
  filter (both still hard-coded to `proposed_item_type === "assertion"` pending TASK-012). The
  backend route itself is **not** artificially restricted — `edit_proposal`'s own
  `_load_and_validate_for_edit` (`pipeline.py:154-157`) has no type check, unlike
  `_load_and_validate_for_review` — so TASK-012 can reuse this same endpoint unchanged for the
  other 3 types once it lands.
- **No history/version viewer or diff UI.** No mockup models one, and TASK-006's own acceptance
  criteria explicitly excluded restore/rollback — this ticket only writes new versions, it doesn't
  add a way to browse or compare them.
- **No display of `edited_by`/`edited_at`** in the metadata table. No mockup precedent; the
  `EDITED` status badge already communicates that an edit happened. A future ticket can add this if
  Cleo wants it surfaced.
- **No edit affordance on `Validation.jsx` rows.** `pekopeko-workflow.html` is read-only by design
  (confirmed via its own README section and markup, no `contenteditable`/textarea/edit button
  anywhere in its note rows) — editing stays Detail-screen-only, matching
  `BACKLOG-CLAUDE-V2.md`'s own wording ("l'écran Détail").
- **No client-side dirty-diffing.** Sauvegarder always sends the full current draft, even if
  unchanged from the original — `edit_proposal` tolerates this (creates an extra but harmless
  `history/` version); not treated as a defect worth extra code for V1.
- **No "unsaved changes" guard** on Précédent/Suivant while mid-edit — leaving the page mid-edit
  simply discards the draft, same as Annuler.
- `valid_from`/`valid_until` are edited as plain text inputs, not date pickers — TASK-006 does not
  define or validate a specific date format for these fields, so no format is assumed here either.

## Requirements

- **Backend**: Python/Flask only, no new dependency. Follows the exact `/accept`/`/reject`
  conventions (Scope item 1) — no new error-handling mechanism, no new blueprint.
- **Frontend**: React function components, existing `api/client.js`/`api/review.js` wrappers, no
  new frontend dependency. No direct `fetch()` outside `api/client.js` (project-wide convention,
  verified by grep in every prior ticket's verification record).

## Constraints

- No change to `review.edit_proposal`'s signature or behavior (TASK-006 is not reopened).
- No change to `ProposalSummary`/`ProposalDetail`'s JSON shape.
- No new backend endpoint beyond the one route in Scope item 1.
- No file under `src/app/review/` is modified — only `src/app/api/` (route, serialization, error
  mapping).
- No auth change — the new route sits behind the same `X-API-Key` check as every other route
  (`app.py`'s `before_request`, unchanged).

## Files/modules concerned

- **Backend**: `src/app/api/routes_review.py` (new route), `src/app/api/serialization.py` (new
  `edit_result_to_dict`), `src/app/api/app.py` (import + one `ERROR_STATUS_MAP` row). New tests in
  `src/tests/api/` mirroring the existing accept/reject route tests (success; missing
  `reviewer_id`; disallowed `field_updates` key → 400; wrong status → 409; domain mismatch → 400;
  empty body+field_updates → 400).
- **Frontend**: `frontend/src/api/review.js` (`editProposal`), `frontend/src/pages/ProposalDetail.jsx`
  (edit-mode state/UI), `frontend/src/pages/Validation.jsx` (EDITED-inclusive queue fetch),
  `frontend/src/index.css` (edit-mode classes). New/updated tests: `review.test.js`
  (`editProposal`), `ProposalDetail.test.jsx` (toggle, save success/failure, cancel, allow-listed
  fields only), `Validation.test.jsx` (an `EDITED`-status proposal still appears in the queue).

## Dependencies

TASK-006 (`completed` — the mechanism this ticket exposes), TASK-007 (`completed` — API
conventions extended here), TASK-010, TASK-011 (`completed` — pages edited here). Independent of
TASK-005/TASK-012 (Entity/Event/Relationship) — not blocked by either, per the assertion-only
scoping above.

## Acceptance criteria

Backend:

1. `POST /domains/<domain>/proposals/<proposal_id>/edit` exists on `review_bp`, requires
   `reviewer_id` in the JSON body; a missing/empty `reviewer_id` produces the same `400
   ReviewValidationError` accept/reject already produce for the same condition.
2. A valid call with `body` and/or `field_updates` calls `review.pipeline.edit_proposal` with
   those exact values and returns `200` with
   `{proposal_id, edited_by, edited_at, archived_version_path (string), archived_version}`.
3. A `field_updates` key outside `EDITABLE_FIELDS_BY_TYPE[proposed_item_type]` (e.g. `id` or
   `domain` for an assertion) → `UneditableFieldError` → `400` with
   `error.type == "UneditableFieldError"`.
4. Editing a proposal whose `proposal_status` is not `PROPOSED`/`EDITED` (e.g. already `ACCEPTED`)
   → `InvalidProposalStatusError` → `409` (already-mapped, verified reachable through this route).
5. A `domain` in the URL that doesn't match the proposal's own `domain` field →
   `DomainMismatchError` → `400` (already-mapped, verified reachable through this route).
6. Both `body` and `field_updates` omitted or empty → `ValidationError` → `400`.
7. A successful edit is verified end-to-end: a subsequent
   `GET /domains/<domain>/proposals/<proposal_id>` reflects the new `body`/`epistemic_status`/
   `valid_from`/`valid_until`, `proposal_status: "EDITED"`, `edited_by`, `edited_at`; and a
   `history/` snapshot file exists on disk (same on-disk verification style TASK-006's own tests
   use).
8. The route follows the exact conventions of `/accept`/`/reject`: `_check_domain` guard,
   `request.get_json(silent=True) or {}`, `jsonify(...), 200` on success — no deviation verified by
   direct code comparison.

Frontend:

9. `editProposal` in `api/review.js` POSTs to `/domains/<domain>/proposals/<id>/edit` with the
   `{reviewer_id, body, field_updates}` shape (mocked-fetch test).
10. `ProposalDetail.jsx` renders a "✎ Éditer" toggle whenever Accepter/Rejeter are shown; clicking
    it replaces the content display with a textarea seeded with the current `body`, the
    `epistemic_status` row with a select seeded with the current value, and the `valid_from`/
    `valid_until` row with text inputs seeded with their current values — no other metadata field
    becomes editable.
11. While in edit mode, Rejeter/Accepter/✎Éditer are hidden and Sauvegarder/Annuler are shown
    instead.
12. Sauvegarder calls `editProposal` with the current draft values, then refetches `getProposal`
    and exits edit mode on success; a mocked failure response surfaces through the existing
    `actionError` banner and edit mode stays open with the draft intact.
13. Annuler exits edit mode and discards the draft without calling `editProposal`.
14. After a successful edit (mocked `getProposal` returning `proposal_status: "EDITED"`), the
    status bar renders the "Éditée" label with `.proposal-status-badge.EDITED` styling — regression
    check only, no new code should be required for this to pass since both already exist.
15. Accepter/Rejeter continue to work unchanged (calling `acceptProposal`/`rejectProposal` exactly
    as before) on a proposal whose `frontmatter.proposal_status` is `EDITED`.
16. A fixture where `listProposals` is mocked separately for `status: "PROPOSED"` and
    `status: "EDITED"` shows both sets merged into `Validation.jsx`'s displayed queue and into
    `ProposalDetail.jsx`'s Précédent/Suivant navigation.
17. No entity/event/relationship proposal gains an edit affordance from this ticket (scope stays
    behind the existing `proposed_item_type === "assertion"` filters).
18. No file under `src/` is modified by the frontend half of this ticket.

## Testing requirements

- **Backend**: `pytest`, Flask `test_client()` tests in `src/tests/api/` mirroring the existing
  accept/reject route test structure, covering AC1-8. No test against a real vault outside a
  `tmp_path`-backed fixture (project-wide convention).
- **Frontend**: Vitest + React Testing Library, mocked `fetch`/API modules only (no real network
  calls), covering AC9-17.
- Project-wide bar: **at least 80% coverage** on every file touched.

## Out of scope

- Entity/event/relationship editing — deferred to whenever TASK-012 lands and lifts
  `Validation.jsx`/`ProposalDetail.jsx`'s type filters; the backend route needs no change to
  support it then (see V1 scope decisions).
- History/version viewer, diff view, restore/rollback — no mockup, and explicitly excluded by
  TASK-006's own acceptance criteria.
- Displaying `edited_by`/`edited_at` in the UI.
- Any edit affordance on `Validation.jsx`.
- Folder-path builder (TASK-014), bulk actions (TASK-015) — same GUI-socle boundary as
  TASK-010/TASK-011/TASK-012.
- Any change to `review/edit_proposal`'s signature, the `history/` mechanism, or
  `EDITABLE_FIELDS_BY_TYPE` — TASK-006 is not reopened.
