# TASK-014a: Context Field — Storage, Path Placement, Scoped Scan (All Item Types)

- **Status**: completed

## Objective

Implement ADI-016's structural half: give `context` a real, first-class place in storage for all
four canonical item types — assertion, entity, event, relationship — not just assertion the way
ADI-012's `proposed_path_segments` stayed. This is the "field/path/storage" side of the same split
ADI-012/TASK-014 (structure) and TASK-001e (LLM value-population) already used: this ticket makes
`context` a real, writable, editable, path-affecting field; **TASK-014b** (its own ticket, blocking
dependency on this one) makes the LLM/ingestion pipeline actually propose a value for it. This
ticket does not populate `context` from anywhere — every acceptance criterion here uses a
hand-supplied value.

Extends TASK-002 (`completed`, `assertion_path`/`write_assertion_file`), TASK-005 (`completed`,
`entity_path`/`event_path`/`relationship_path`/`write_entity_file`/`write_event_file`/
`write_relationship_file`), and TASK-006 (`completed`, `EDITABLE_FIELDS_BY_TYPE`) additively — same
posture already used by every prior satellite in this chain: no change to any existing function's
*required* parameters, full backward compatibility for every file already on disk.

**No dependency on TASK-001f or TASK-014b.** Every acceptance criterion below is testable by
passing a hand-set `context` string directly to the functions this ticket changes — this ticket is
independently completable before either of those land, the same way TASK-014's own backend half
was independently testable ahead of its frontend's TASK-013 dependency.

## Binding context (references, not duplicated here)

- **ADI-016** (`specs/decisions/ADI-016-context-universe-first-class-field.md`, Accepted): the
  decision this ticket implements — read it in full before implementing anything here, it is the
  binding contract for field shape, path placement, and what is explicitly out of scope.
- **ADI-012** (`specs/decisions/ADI-012-folder-path-organization.md`, Accepted): this ticket does
  not touch `proposed_path_segments`' scope — `context` is a separate, narrower, cross-type
  parameter, not an extension of taxonomy segments to new types. **Correction 2026-09-07**: this
  bullet previously described ADI-012 as having decided that `proposed_path_segments` "stays
  assertion-only". It had not: it deferred the extension to entity/event/relationship rather than
  ruling it out. That extension was carried out by **TASK-005a** (`completed`, 2026-09-07), which
  amended the same four `*_path`/`write_*_file` functions this ticket amends — see Dependencies for
  how the two compose (this ticket now builds on TASK-005a's already-landed code, not a symmetric
  race between two still-`backlog` tickets).
- `src/app/review/storage.py:58` (`_COMMON_EDITABLE_FIELDS`), `:100-108` (`_validate_path_segments`
  — reused as-is for validating a single `context` string), `:131-150` (`assertion_path`,
  `entity_path`, `event_path`, `relationship_path`), `:283-307` (`write_entity_file`,
  `write_event_file`, `write_relationship_file`; `write_assertion_file` sits just above at
  `:265-280`ish, already taking `path_segments` from TASK-014) — the exact functions this ticket
  amends.
- `src/app/review/pipeline.py:239-321` (`accept_proposal`) — the four type-dispatched branches
  (`:252` assertion, `:271` entity, `:286` event, `:303` relationship), each ending in its own
  `write_*_file` call. This ticket adds one line to each branch.
- `src/app/ingestion/storage.py` (`scan_existing_assertion_folders`, `scan_proposed_path_segments`
  — added by TASK-001e/ADI-014/ADI-015) — the two scan functions this ticket adds an optional
  `context` parameter to.
- TASK-012 (`specs/tasks/completed/TASK-012-entity-event-relationship-review-gui.md`, `completed`):
  `EntityTypeBadge`/`EventTemporalRange`/`RelationshipEndpoints` — the existing per-type display
  components in `ProposalDetail.jsx`/`Validation.jsx` this ticket's own `context` display sits
  alongside, without reusing `FolderPathBuilder.jsx` (which stays assertion-taxonomy-specific, per
  ADI-016's own Consequences).
- TASK-013 (`specs/tasks/completed/TASK-013-proposal-edit-frontend.md`, `completed`): the generic
  `field_updates`/`editProposal` edit mechanism this ticket's frontend half plugs `context` into,
  the same way TASK-014 already plugged `proposed_path_segments` into it.

## Scope

### Backend

1. `review/storage.py`: `assertion_path`, `entity_path`, `event_path`, `relationship_path` each
   gain an optional `context: Optional[str] = None` parameter, inserted as a single path component
   directly under the type-plural folder and before any further segments:
   - `assertion_path(vault_root, domain, assertion_id, path_segments=None, context=None)` →
     `vault_root/domain/assertions/[context/]*path_segments/assertion_id/assertion_id.md`.
   - `entity_path(vault_root, domain, entity_id, context=None)` →
     `vault_root/domain/entities/[context/]entity_id/entity_id.md` (and symmetrically for
     `event_path`/`relationship_path`).
   - `context=None` (default) produces exactly today's path for every type — byte-identical
     regression, verified by test.
   - Validated via the existing `_validate_path_segments` helper, called with `[context]` when
     `context` is not `None` (reuses the same non-empty/no-`/`/no-`..` check already applied to
     taxonomy segments — `context` is just one more path component, no new validation logic
     needed).
2. `write_assertion_file`, `write_entity_file`, `write_event_file`, `write_relationship_file` each
   gain the same optional `context: Optional[str] = None` parameter, passed straight through to
   their respective `*_path` function.
3. `review/pipeline.py::accept_proposal`: each of the four type branches (`:252-321`) reads
   `frontmatter.get("context")` and passes it as `context=` to its `write_*_file` call — symmetric,
   one line added per branch, no other change to `accept_proposal`'s body or its public signature
   (`accept_proposal(vault_root, domain, proposal_id, reviewer_id)` unchanged).
4. `_COMMON_EDITABLE_FIELDS` (`:58`) gains `"context"` directly: `_COMMON_EDITABLE_FIELDS = {"body",
   "epistemic_status", "valid_from", "valid_until", "context"}` — applies to all four types
   uniformly through the existing `EDITABLE_FIELDS_BY_TYPE` dict comprehension/construction,
   deliberately *not* the type-scoped form TASK-014 chose for `proposed_path_segments` (ADI-016
   requires `context` to be cross-type from the start).
5. `ingestion/storage.py::scan_existing_assertion_folders(vault_root, domain, context=None)` and
   `scan_proposed_path_segments(vault_root, domain, context=None)`: when `context` is given, scan
   is restricted to `<vault_root>/<domain>/assertions/<context>/` instead of
   `<vault_root>/<domain>/assertions/`; `context=None` (default) preserves today's whole-domain
   scan exactly, unchanged for every existing caller.

### Frontend

6. New small component (or a focused addition to `ProposalDetail.jsx` directly, decided during
   implementation based on whichever is less code — no premature abstraction) rendering a
   `context` chip/badge: read-only text when not editable, an inline text input when editable
   (simpler than `FolderPathBuilder`'s dropdown-per-segment UI, since `context` is a single
   optional string, not a list) — shown for **all four** proposal types in `ProposalDetail.jsx`'s
   metadata card, alongside the existing type-specific components
   (`EntityTypeBadge`/`EventTemporalRange`/`RelationshipEndpoints`/`FolderPathBuilder`).
7. `ProposalDetail.jsx`'s edit mode gains a `draftContext` field (seeded from
   `frontmatter.context` on entering edit mode, alongside the existing `draftPathSegments` etc.);
   Sauvegarder's `field_updates` includes `context: draftContext` for every type (not
   assertion-gated, since `context` is now common to all four).
8. `Validation.jsx`: read-only `context` display added to `NoteRow` for all four types (no new edit
   affordance here — same precedent TASK-013 established and TASK-014 followed for its own
   assertion-only column; editing happens in `ProposalDetail.jsx`).

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **No `FolderPathBuilder.jsx` reuse for `context`.** `FolderPathBuilder` is built around a list of
  freely-addable/reorderable taxonomy segments; `context` is a single optional string. Reusing it
  would mean either crippling most of its UI (dropdown, "+ Ajouter", drag-reorder — all meaningless
  for a length-≤1 value) or adding a "single-value mode" flag that complicates a component built
  for a different concept. A plain text field is simpler and matches what `context` actually is.
- **No dedicated `GET .../organization-folders`-style endpoint for `context` values.** Unlike
  taxonomy segments (which benefit from "existing folders at this level" suggestions), `context`
  is expected to be a small, stable, low-cardinality set per domain (a handful of ongoing
  novels/projects) — a plain text field is sufficient for V1; a suggestions dropdown can be added
  later if reviewers find themselves retyping values, without this ticket blocking on it.
- **No retroactive relocation.** Same as ADI-012/TASK-014: setting `context` on an edit never moves
  an already-`ACCEPTED` canonical file. Only affects the physical path chosen at the moment
  `accept_proposal` runs.
- **Ungating the "✎ Éditer" button carries a prerequisite** (added 2026-09-07). **Resolved by
  TASK-005a, 2026-09-07 (`completed`) — no longer this ticket's problem.** This bullet originally
  warned that this ticket's frontend half (§7) needs edit mode for all four types, but
  `ProposalDetail.jsx` gated that button on `assertion`, and ungating it without also widening
  `_COMMON_EDITABLE_FIELDS` to cover `proposed_path_segments` would produce `UneditableFieldError` →
  `400` on every entity/event/relationship save. TASK-005a has since ungated the button and moved
  `proposed_path_segments` into `_COMMON_EDITABLE_FIELDS` (its own §A4/§E14). By the time this
  ticket is implemented, the button is already ungated and that half of the allow-list already
  widened — this ticket only needs to add `"context"` to `_COMMON_EDITABLE_FIELDS` additively, same
  as any other field in this shared set.

## Requirements

- **Backend**: Python/Flask only, no new dependency. Same testing discipline as TASK-014:
  `pytest`, direct function calls plus `tmp_path`-backed vault fixtures for path/scan tests.
- **Frontend**: React function components, existing `api/review.js`/`api/client.js` wrappers, no
  new frontend dependency, no direct `fetch()` outside `api/client.js`.

## Constraints

- No change to `accept_proposal`'s, any `*_path`'s, or any `write_*_file`'s *required* parameters —
  `context` is additive-optional throughout, matching every prior satellite in this chain.
- No change to `edit_proposal`'s mechanism, signature, or `history/` versioning logic (TASK-006 is
  not reopened beyond the one `_COMMON_EDITABLE_FIELDS` line).
- No new backend blueprint, no new route.
- **Correction 2026-09-07**: this bullet originally said `proposed_path_segments`/taxonomy segments
  "remain assertion-only" and deferred that gap to future TASK-005/012-descendant work. **TASK-005a
  has since landed (`completed`, 2026-09-07)** and extended taxonomy segments to entity/event/
  relationship — so this is no longer true, and there is nothing left for a hypothetical future
  ticket to close on that front. `context` (this ticket's own field) is still a separate, narrower,
  cross-type concept from taxonomy segments (per ADI-016) — this ticket does not touch
  `proposed_path_segments` itself, it only adds `context` alongside it.
- No file under `src/app/extraction/` or `src/app/ingestion/providers/`, `pipeline.py` is touched
  by this ticket (that's TASK-014b's scope) — this ticket only changes `review/storage.py`,
  `review/pipeline.py`, and `ingestion/storage.py`'s two scan functions.

## Files/modules concerned

- **Backend**: `src/app/review/storage.py` (`assertion_path`, `entity_path`, `event_path`,
  `relationship_path`, `write_assertion_file`, `write_entity_file`, `write_event_file`,
  `write_relationship_file`, `_COMMON_EDITABLE_FIELDS`), `src/app/review/pipeline.py`
  (`accept_proposal`, all 4 branches), `src/app/ingestion/storage.py`
  (`scan_existing_assertion_folders`, `scan_proposed_path_segments`). New/updated tests in
  `src/tests/review/` (path construction with/without `context` for all 4 types, regression checks
  that `context=None` matches today's path byte-for-byte, `_COMMON_EDITABLE_FIELDS`/
  `EDITABLE_FIELDS_BY_TYPE` regression for all 4 types) and `src/tests/ingestion/` (scoped-scan
  behavior: `context` sub-tree vs. whole-domain default).
- **Frontend**: `frontend/src/pages/ProposalDetail.jsx` (new `context` display/edit for all 4
  types, `draftContext`, save payload), `frontend/src/pages/Validation.jsx` (read-only `context`
  column/cell for all 4 types), new or extended component for the `context` chip. New/updated
  tests: `ProposalDetail.test.jsx`, `Validation.test.jsx`.

## Dependencies

TASK-002/TASK-005/TASK-006 (`completed`, amended here), ADI-016 (Accepted, binding contract). No
dependency on TASK-001f or TASK-014b — see Objective.

**Soft-coupled to TASK-005a** (`completed`, 2026-09-07 — ADI-012 adoption for entity/event/
relationship), not a blocking dependency in either direction: this ticket remains independently
implementable without it. The two tickets amend **the same** four `*_path` and four `write_*_file`
functions and both touch `_COMMON_EDITABLE_FIELDS`; since TASK-005a has already landed, this
ticket's own implementation composes **onto** the real, already-extended signatures below (each
`*_path`/`write_*_file` already has `path_segments`) rather than racing them — add `context` as the
next additive-optional parameter, in the same position ADI-016 already specifies (context first,
taxonomy segments after):

```
entity_path(vault_root, domain, entity_id, path_segments=None, context=None)
  -> <domain>/entities/<context>/<segments...>/<entity_id>/<entity_id>.md
```

— exactly the shape ADI-016 already specifies for assertions (`context` first, taxonomy segments
after). The second to land composes with the first rather than replacing it, same precedent as the
`write_source_file` signature change shared between TASK-016 and TASK-017. See also the edit-button
prerequisite in V1 scope decisions, which both tickets share.

## Acceptance criteria

Backend:

1. `assertion_path(vault_root, domain, assertion_id)` (no `context`, or `context=None`) returns
   exactly today's path — regression test.
2. `assertion_path(vault_root, domain, assertion_id, context="tatouages")` returns
   `vault_root/domain/assertions/tatouages/assertion_id/assertion_id.md`.
3. `assertion_path(..., path_segments=["a","b"], context="tatouages")` returns
   `vault_root/domain/assertions/tatouages/a/b/assertion_id/assertion_id.md` (context precedes
   taxonomy segments).
4. `entity_path`/`event_path`/`relationship_path` each support the same `context=None` regression
   and `context="x"` insertion behavior as AC1-2, symmetrically.
5. A `context` value containing `/` or equal to `..` is rejected before any write, same
   `ValidationError`/`400` convention as an invalid taxonomy segment — no partial state.
6. `accept_proposal` on a Proposal of each of the four types, with `context: "tatouages"` in its
   frontmatter, writes the canonical file under the context-segmented path for that type.
7. `accept_proposal` on a Proposal with `context` absent or `null` writes to the plain path for
   that type — no regression, no error, for all four types.
8. `context` is accepted via `edit_proposal`'s `field_updates` for **every** `proposed_item_type`
   (assertion, entity, event, relationship) — a subsequent `GET` reflects the new value, and a
   `history/` snapshot exists.
9. `scan_existing_assertion_folders(vault_root, domain)` (no `context`) behaves exactly as before
   TASK-014a — regression test.
10. `scan_existing_assertion_folders(vault_root, domain, context="tatouages")` against a vault
    containing assertions both inside and outside `assertions/tatouages/` returns only paths from
    within that sub-tree. `scan_proposed_path_segments` behaves symmetrically.

Frontend:

11. `ProposalDetail.jsx` renders the `context` value (or a clear empty/placeholder state when
    `None`) for all four proposal types outside edit mode.
12. Entering edit mode seeds `draftContext` from `frontmatter.context`; Sauvegarder's
    `editProposal` call includes `context: draftContext` in `field_updates` for all four types.
13. `Validation.jsx`'s `NoteRow` renders each note's `context` read-only for all four types, with
    no edit affordance on that page (regression-consistent with TASK-013/014's own precedent).
14. No file under `src/app/extraction/` or `src/app/ingestion/providers/`/`pipeline.py` is modified
    by this ticket (regression check, mirrors TASK-001e's/TASK-014a's own out-of-scope boundary).

## Testing requirements

`pytest` (backend) / Vitest + React Testing Library (frontend), covering AC1-14. Project-wide bar:
at least 80% coverage on every file touched.

## Out of scope

- Populating `context`'s value from anything (source folder, LLM) — that is TASK-014b's entire
  scope; every test here uses a hand-supplied value.
- Extending `proposed_path_segments`/taxonomy to entity/event/relationship (remains ADI-012's own
  deferred scope, see Constraints).
- Entity/relationship dedup-by-context (no dedup mechanism exists at all yet, see ADI-016).
- A `context`-values suggestions endpoint/dropdown (see V1 scope decisions).
- Retroactive relocation of already-canonical files.

## Verification record (2026-09-08)

Verified by Claude in the same session as implementation — same disclosed limitation as every prior
ticket in this project: not a second independent reviewer. Implemented together with TASK-014b in
one session at Cleo's explicit request; this record covers TASK-014a's own scope only (see
TASK-014b's own file for its half). One deliberate deviation from the ticket's literal §Scope wording
was confirmed with Cleo before implementing, not silently resolved: `accept_proposal`'s four branches
write `"context"` as a real key into `item_frontmatter` (not just pass `context=` to `write_*_file`),
matching ADI-016's explicit "first-class frontmatter field... queryable" language (it compares
`context` directly to `valid_until`, an existing literal key) over the ticket's own "no other change
to `accept_proposal`'s body" phrasing, which would have left `context` purely path-affecting like
`proposed_path_segments` — the ticket text is arguably imprecise here, flagged rather than silently
picked.

- `[PASS]` `pytest src/tests/review --cov=src/app/review`: **181/181 pass**, 100% coverage on every
  file in the package.
- `[PASS]` `pytest src/tests/ingestion --cov=src/app/ingestion`: **139/139 pass** (scoped-scan tests
  for this ticket, plus TASK-014b's own additions) plus the same 2 pre-existing, unrelated failures
  every ticket since TASK-014 has documented (`test_comprehensive.py::test_acceptance_criteria_compliance`,
  `test_pipeline.py::test_import_isolation`) — reconfirmed via `git stash`/re-run/`git stash pop` that
  both fail identically without this session's changes.
- `[PASS]` `npx vitest run` (frontend): **113/113 pass**, including the new `ContextValue.jsx` and its
  usage in `ProposalDetail.jsx`/`Validation.jsx`.
- `[PASS]` `npx vite build`: succeeds, no errors.
- `[PASS]` Manual end-to-end reproduction (see TASK-014b's own Verification record — the two tickets
  were verified together via one script exercising the full chain, since TASK-014a's structural half
  has no independent effect without TASK-014b's value population).

Acceptance criteria checked one by one:

- `[PASS]` AC1 `assertion_path` no-context regression (byte-identical to pre-ticket output).
- `[PASS]` AC2 `assertion_path(..., context="tatouages")` inserts under the type-plural folder.
- `[PASS]` AC3 context precedes taxonomy segments when both are given.
- `[PASS]` AC4 same regression + insertion behavior for `entity_path`/`event_path`/`relationship_path`.
- `[PASS]` AC5 a `context` containing `/` or `..` is rejected (`ValidationError`) before any write,
  for all 4 types — verified no directory is created on disk when rejected.
- `[PASS]` AC6 `accept_proposal` with `context` in frontmatter writes to the context-segmented path,
  for all 4 types, and (per the confirmed design decision above) the canonical file's own frontmatter
  carries `context` too.
- `[PASS]` AC7 `accept_proposal` with `context` absent/null writes the plain path, `context: null` in
  the canonical frontmatter, no regression, for all 4 types.
- `[PASS]` AC8 `context` accepted via `edit_proposal`'s `field_updates` for every `proposed_item_type`,
  with a `history/` snapshot.
- `[PASS]` AC9 `scan_existing_assertion_folders` no-context regression.
- `[PASS]` AC10 `scan_existing_assertion_folders(..., context=...)` scoped to that subtree only;
  `scan_proposed_path_segments` behaves symmetrically (frontmatter-filtered, since proposals have no
  context subfolders) — including the `context=None` "still returns everything" regression guard a
  naive unconditional filter would have silently broken.
- `[PASS]` AC11 `ProposalDetail.jsx` renders `context` (or a clear empty state) for all 4 types outside
  edit mode.
- `[PASS]` AC12 edit mode seeds `draftContext`; Sauvegarder's `field_updates` includes `context` for
  all 4 types.
- `[PASS]` AC13 `Validation.jsx`'s `NoteRow` renders `context` read-only for all 4 types, no edit
  affordance.
- `[PASS]` AC14 no file under `src/app/extraction/` or `src/app/ingestion/providers/`/`pipeline.py` was
  modified by this ticket's own commits (those changes belong to TASK-014b, tracked separately).
