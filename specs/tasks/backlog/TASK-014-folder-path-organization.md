# TASK-014: Folder-Path Organization — Backend API + Frontend Builder (Assertions, V1)

- **Status**: backlog

## Objective

Implement the "folder-path builder" `BACKLOG-CLAUDE-V2.md`'s TASK-014 entry describes: *"Backend
: API listant/créant les dossiers d'organisation au-delà du chemin fixe `<domain>/<type>/<id>/`
utilisé jusqu'ici. Frontend : intègre le folder path builder interactif des maquettes
(`[segment ▼] / [segment ▼] [+ Ajouter]`) dans les écrans Validation (TASK-010) et Détail
(TASK-011/012)."* Both screens shipped without it (TASK-010/011, both `completed`), staying on
the plain fixed canonical path from ADI-004 — deferred to this ticket by design, not a cut.

Writing this ticket surfaced a real architecture question ADI-004 deliberately left open: does
the chosen path change where the canonical file physically lives, or is it separate metadata?
That question was resolved with Cleo *before* this ticket, as **ADI-012** (folder-path-
organization, Accepted 2026-09-04) — read it in full before implementing anything here, it is
the binding contract for the new file layout, not a restatement of ADI-004.

**Scope: `assertion` only.** Same MVP boundary TASK-010/011/013 already use — `Validation.jsx`/
`ProposalDetail.jsx` still filter to `proposed_item_type === "assertion"` pending TASK-012. The
backend pieces here (path-segment field, canonical writer change, folders-listing endpoint) are
written generically enough that TASK-012 can extend them later for the other three types, but
this ticket does not implement that extension itself — same posture TASK-013 already took for
`edit_proposal`.

**Dependency note**: this ticket's frontend half needs `editProposal` (TASK-013, `backlog`, not
yet implemented) to exist — folder-path edits are sent through the exact same endpoint as
`body`/`epistemic_status` edits, not a new one. TASK-013 must land first, or alongside this
ticket, before the frontend scope below is implementable.

## Binding context (references, not duplicated here)

- **ADI-012** (`specs/decisions/ADI-012-folder-path-organization.md`, Accepted): the new
  canonical layout — `<vault_root>/<domain>/<item-type-plural>/<segment_1>/.../<segment_n>/
  <item_id>/<item_id>.md`, domain fixed first, item-type folder directly under domain, segments
  empty by default (bit-identical to today's path). This ticket implements it for `assertion`.
- **TASK-002** (`specs/tasks/completed/TASK-002-proposal-review-workflow.md`, `completed`):
  `review/storage.py:92-93` (`assertion_path`), `:185-191` (`write_assertion_file`),
  `review/pipeline.py:204-245` (`accept_proposal`) — the exact functions this ticket amends
  additively, same category of change TASK-001a/b/c/d already made to TASK-001/TASK-003.
- **TASK-006** (`specs/tasks/completed/TASK-006-proposal-edit-and-history.md`, `completed`):
  `review/storage.py:42-49` — `_COMMON_EDITABLE_FIELDS`/`EDITABLE_FIELDS_BY_TYPE`, the allow-list
  this ticket adds one entry to. `edit_proposal`'s mechanism itself (`review/pipeline.py`) is
  **not modified** — a field in the allow-list is edited exactly like `body`/`epistemic_status`
  already are, versioned into `history/` the same way, no special-casing needed.
- **TASK-013** (`specs/tasks/backlog/TASK-013-proposal-edit-frontend.md`, `backlog`): the
  `POST /domains/<domain>/proposals/<proposal_id>/edit` route and `ProposalDetail.jsx` edit mode
  this ticket's frontend plugs into — **blocking dependency**, see Objective.
- **TASK-001e** (`specs/tasks/backlog/TASK-001e-extraction-proposed-folder-path.md`, `backlog`):
  the satellite that makes `proposed_path_segments` non-empty out of extraction. Non-blocking —
  this ticket must work correctly with every Proposal's `proposed_path_segments` starting `[]`
  (same graceful-degradation posture TASK-011 already used for TASK-001a/TASK-001b).
- **TASK-010**/**TASK-011** (`completed`): `frontend/src/pages/Validation.jsx` and
  `frontend/src/pages/ProposalDetail.jsx`, both read in full while writing this ticket — see
  Scope for their exact insertion points and current line numbers.
- `specs/ux-design/README.md` ("Interactive Folder Path Builder" section) and the two mockups'
  JS: `pekopeko-proposal-detail.html:1525-1613` (`toggleFolderDropdown`, `selectFolder`,
  `createNewFolder`, `addFolderSegment`, `updatePathData`) and the equivalent block in
  `pekopeko-workflow.html:1226-1330` — the interaction pattern to port to React as *controlled
  state*, not the DOM-mutation approach the static mockup uses (same "reference, not literal
  port" posture TASK-013 already used for its own mockup section). Per `specs/ux-design/README.md`,
  clicking a segment shows existing values as a dropdown plus "+ Créer nouveau...", and a
  trailing "+ Ajouter" button appends a new trailing segment.
- `src/app/review/storage.py:84-85` (`_generate_assertion_id`, `f"assert-{uuid.uuid4()}"`) — the
  id prefix the folders-listing endpoint (Scope item 4) uses to tell a taxonomy segment apart
  from an item's own id folder.

## Scope

### Backend

1. `review/storage.py::assertion_path(vault_root, domain, assertion_id)` gains an optional
   parameter: `assertion_path(vault_root, domain, assertion_id, path_segments=None)`. When
   `path_segments` is `None` or `[]`, the returned path is byte-identical to today's
   (`vault_root / domain / "assertions" / assertion_id / f"{assertion_id}.md"`). When non-empty,
   each segment is inserted as its own path component between `"assertions"` and
   `assertion_id`: `vault_root / domain / "assertions" / *path_segments / assertion_id /
   f"{assertion_id}.md"`.
2. `review/storage.py::write_assertion_file(vault_root, domain, frontmatter, body)` gains the
   same optional `path_segments=None` parameter, passed straight through to `assertion_path`.
3. `review/pipeline.py::accept_proposal` reads `frontmatter.get("proposed_path_segments", [])`
   from the Proposal being accepted and passes it to `write_assertion_file` as `path_segments`.
   No other change to `accept_proposal`'s body or its public signature
   (`accept_proposal(vault_root, domain, proposal_id, reviewer_id)` unchanged).
4. `review/storage.py::EDITABLE_FIELDS_BY_TYPE["assertion"]` (currently
   `_COMMON_EDITABLE_FIELDS = {"body", "epistemic_status", "valid_from", "valid_until"}`, line 42)
   gains `"proposed_path_segments"` — either by adding it to `_COMMON_EDITABLE_FIELDS` directly
   (if a future entity/event/relationship extension would want it too — plausible given ADI-012's
   type-agnostic naming, but not this ticket's call to make) or as a new
   `_COMMON_EDITABLE_FIELDS | {"proposed_path_segments"}` entry scoped to `"assertion"` only,
   matching the ticket's own assertion-only scope more conservatively. **Pick the assertion-only
   form** unless a concrete reason to widen it now surfaces during implementation — narrower is
   easier to widen later than the reverse.
5. New read-only route on the existing `review_bp` (no new blueprint, same convention TASK-013
   already followed for `/edit`):
   `GET /domains/<domain>/organization-folders?item_type=assertion`. Handler scans
   `<vault_root>/<domain>/assertions/` recursively; at each directory level, a folder name
   matching `^assert-` (same prefix `_generate_assertion_id` produces) is treated as an item's own
   id folder — a leaf, not descended into further — every other folder name is a taxonomy
   segment, collected and recursed into. Returns the distinct segment values grouped by depth
   (e.g. `{"segments_by_depth": [["mythologie", "livres"], ["japonaise", "histoire"], ...]}` —
   exact response shape to be finalized during implementation, following `serialization.py`'s
   existing dict-building style) so the frontend can offer "existing folders at this level" in
   each dropdown, matching the mockup's own per-segment dropdown behavior. `item_type` query
   param is required and validated against `"assertion"` only for now (`400` on anything else,
   same `ValidationError` convention as TASK-007a's pagination params) — kept as an explicit
   parameter rather than hard-coded so TASK-012 can extend it later without a route signature
   change.
6. `src/app/api/app.py`: no new error mapping needed — the new route's only failure modes are
   `_check_domain`'s existing `DomainMismatchError`/`404` path and the new `item_type`
   `ValidationError`, both already mapped.

**V1 scope decision — no folder-creation endpoint** (explicit deviation from
`BACKLOG-CLAUDE-V2.md`'s literal "API listant/**créant**"): a new segment is a plain client-side
value (typed by the reviewer, held in React state) until an actual `accept_proposal` call writes
an assertion under it — the directory then exists on disk exactly the way `<id>/` folders already
come into existence today (as a side effect of `_write_atomic_file`'s parent-directory creation,
not a separate `mkdir` call). No endpoint creates an *empty* organization folder ahead of any
item being saved there. Reasoning: ADI-002/ADI-006 already establish that nothing derived is
persisted in the vault separately from canonical files themselves; a "pre-created, itemless
folder" would be a new category of non-canonical, non-derived vault state this corpus doesn't
otherwise have. Flagged here for Cleo to push back on if the literal mockup behavior (a folder
that shows up in future dropdowns the instant "+ Créer nouveau" is clicked, even before any item
is saved there) is actually required.

### Frontend

7. New component `frontend/src/components/FolderPathBuilder.jsx` — controlled React component,
   not a DOM-mutating port of the mockup's vanilla JS (`toggleFolderDropdown`/`selectFolder`/etc.
   become local component state + callbacks instead). Props: `segments: string[]`,
   `optionsByDepth: string[][]` (from Scope item 5's endpoint response), `editable: boolean`,
   `onChange: (newSegments: string[]) => void`. Renders one `.folder-segment` per entry in
   `segments` (each a button that, when `editable`, opens a `.folder-dropdown` listing
   `optionsByDepth[index]` plus a "+ Créer nouveau..." option that prompts for a new segment name
   inline — a small local input, not `window.prompt()`, to stay consistent with the rest of the
   React app's UI conventions) plus a trailing "+ Ajouter" button appending a new empty segment.
   When `!editable`, renders the joined path (`segments.join("/")`) as plain text — no dropdowns,
   no add button.
8. `frontend/src/api/review.js`: new `listOrganizationFolders(domain, itemType)` — GET wrapper
   through `api/client.js` (same pattern as every other function in this file; no direct
   `fetch()`).
9. `frontend/src/pages/ProposalDetail.jsx` (depends on TASK-013's edit-mode scope, its own
   ticket item 6, which adds the draft-state machinery this ticket plugs into): the Métadonnées
   card gains a "Dossier proposé" row. Outside edit mode: `FolderPathBuilder` with
   `editable={false}`, `segments={frontmatter.proposed_path_segments || []}`. Entering edit mode
   (TASK-013's toggle) seeds a fifth draft field, `draftPathSegments`, from the same source.
   Inside edit mode: `FolderPathBuilder` with `editable={true}`, `segments={draftPathSegments}`,
   `optionsByDepth` from `listOrganizationFolders(domain, "assertion")` (fetched once when edit
   mode opens, not on every keystroke), `onChange={setDraftPathSegments}`. Sauvegarder
   (TASK-013's own save handler) includes `proposed_path_segments: draftPathSegments` in the same
   `field_updates` object it already sends for `epistemic_status`/`valid_from`/`valid_until` — no
   second `editProposal` call.
10. `frontend/src/pages/Validation.jsx`: each `NoteRow` gains a read-only `FolderPathBuilder`
    (`editable={false}`) showing `note.detail.frontmatter.proposed_path_segments`. **No edit
    affordance added here** — TASK-013 already established "no edit affordance on
    `Validation.jsx` rows" as this project's own precedent (its own ticket, "V1 scope decisions");
    this ticket follows the same line rather than reopening it, even though the mockup's
    `pekopeko-workflow.html` does show the builder as editable inline. Flagged explicitly for
    Cleo: if inline editing directly from Validation is actually wanted, that's a deviation from
    TASK-013's own precedent and should be a conscious call, not something this ticket makes
    silently.
11. `frontend/src/index.css`: port `.folder-path-builder`/`.folder-segment`/`.folder-segment-btn`/
    `.folder-dropdown`/`.folder-dropdown-item`/`.folder-add-btn`/`.folder-separator` classes from
    the mockups (`pekopeko-proposal-detail.html:530-568`-ish and the equivalent block in
    `pekopeko-workflow.html`) — CSS already exists, adapt rather than reinvent, same approach
    every prior GUI ticket (TASK-009/010/011) already took for its own ported blocks.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **Assertion-only** (see Objective) — no entity/event/relationship rendering or writing, even
  though ADI-012's backend pieces are written generically enough to extend later.
- **No folder-creation endpoint** (Scope item 5's own note above).
- **No inline edit affordance on `Validation.jsx`** (Scope item 10's own note above) — read-only
  display only, matching TASK-013's precedent.
- **No retroactive relocation.** This ticket never moves an already-`ACCEPTED` canonical file —
  `path_segments` only affects the physical path chosen at the moment `accept_proposal` runs.
  Existing assertions already on disk under the old fixed layout are untouched and remain
  perfectly valid (ADI-012's own backward-compatibility guarantee).
- **No server-side segment-name sanitization** beyond what's needed for `_write_atomic_file` not
  to break (e.g. rejecting a segment containing `/` or resolving to `..`, which would otherwise
  let a malicious/malformed `field_updates` payload write outside the intended tree) — this is a
  correctness/security guard, not a UX nicety, and must be present; a segment that fails this
  check raises the same `ValidationError`/`400` other malformed `field_updates` already produce
  via `UneditableFieldError`'s sibling checks in `review/storage.py`'s `_validate_editable_fields`
  path (exact error type to decide during implementation — reuse `ValidationError` rather than
  inventing a new type unless a concrete reason not to surfaces).
- **`optionsByDepth` is fetched once per edit-mode session**, not re-fetched on every keystroke
  or dropdown open — stale-by-a-few-seconds existing-folder suggestions are an acceptable V1
  tradeoff (same "fetch on mount, don't over-fetch" posture already used elsewhere in this
  codebase, e.g. `ProposalDetail.jsx`'s own three independent fetches).

## Requirements

- **Backend**: Python/Flask only, no new dependency. New route follows the exact `_check_domain`/
  `jsonify(...), 200` conventions already established by `/accept`/`/reject`/`/edit`.
- **Frontend**: React function components, existing `api/client.js`/`api/review.js` wrappers, no
  new frontend dependency. No direct `fetch()` outside `api/client.js` (verified by grep, same as
  every prior ticket's verification record).

## Constraints

- No change to `accept_proposal`'s, `assertion_path`'s, or `write_assertion_file`'s *required*
  parameters — `path_segments` is additive-optional throughout.
- No change to `edit_proposal`'s mechanism, signature, or the `history/` versioning logic
  (TASK-006 is not reopened beyond the one `EDITABLE_FIELDS_BY_TYPE` line).
- No new backend blueprint.
- No auth change — the new route sits behind the same `X-API-Key` check as every other route.
- No file under `src/app/extraction/` is touched (see TASK-001e's own deviation note — out of
  scope here too).

## Files/modules concerned

- **Backend**: `src/app/review/storage.py` (`assertion_path`, `write_assertion_file`,
  `EDITABLE_FIELDS_BY_TYPE`, new segment-validation helper, new folders-scan helper),
  `src/app/review/pipeline.py` (`accept_proposal`), `src/app/api/routes_review.py` (new
  `GET .../organization-folders` route), `src/app/api/serialization.py` (new response-shaping
  helper for the folders route, if needed). New tests in `src/tests/review/` (path construction
  with/without segments, segment validation rejecting `/`/`..`, `EDITABLE_FIELDS_BY_TYPE`
  regression) and `src/tests/api/` (new route: success, missing/invalid `item_type`, empty vault
  returns empty structure, multi-depth scan correctly separates segments from `assert-*` id
  folders).
- **Frontend**: `frontend/src/components/FolderPathBuilder.jsx` (new),
  `frontend/src/api/review.js` (`listOrganizationFolders`), `frontend/src/pages/ProposalDetail.jsx`
  (Dossier proposé row, draft field, save payload), `frontend/src/pages/Validation.jsx` (read-only
  row addition), `frontend/src/index.css` (ported classes). New/updated tests:
  `FolderPathBuilder.test.jsx` (read-only rendering, dropdown open/select, "+ Créer nouveau",
  "+ Ajouter"), `review.test.js` (`listOrganizationFolders`), `ProposalDetail.test.jsx` (seed,
  edit, save includes `proposed_path_segments`), `Validation.test.jsx` (read-only path renders,
  no edit affordance present).

## Dependencies

TASK-002 (`completed`, amended here), TASK-006 (`completed`, `EDITABLE_FIELDS_BY_TYPE` extended
here), TASK-013 (`backlog`, **blocking** for the frontend half — needs `editProposal` and edit-mode
state machinery), TASK-010/TASK-011 (`completed`, pages edited here), ADI-012 (Accepted,
binding contract for the new layout). TASK-001e (`backlog`, non-blocking — degrades to an empty
initial path). Independent of TASK-005/TASK-012 (assertion-only scope, see Objective).

## Acceptance criteria

Backend:

1. `assertion_path(vault_root, domain, assertion_id)` (no `path_segments`, or `path_segments=[]`/
   `None`) returns exactly the same path as today — regression test against TASK-002's existing
   behavior.
2. `assertion_path(vault_root, domain, assertion_id, path_segments=["a", "b"])` returns
   `vault_root/domain/assertions/a/b/assertion_id/assertion_id.md`.
3. `write_assertion_file(..., path_segments=[...])` writes to the segmented path and the file is
   readable back with correct frontmatter.
4. `accept_proposal` on a Proposal whose frontmatter has `proposed_path_segments: ["x", "y"]`
   writes the canonical assertion file under `.../assertions/x/y/<assertion_id>/<assertion_id>.md`.
5. `accept_proposal` on a Proposal with `proposed_path_segments: []` (or the field entirely
   absent, for a Proposal predating TASK-001e) writes to the plain fixed path — no regression,
   no error.
6. A segment containing `/` or equal to `..` is rejected before any write — `assertion_frontmatter`
   is never written, no partial state, error is a `ValidationError`/`400` (or the type chosen
   during implementation, but must not be a silent no-op or a 500).
7. `proposed_path_segments` is accepted via `edit_proposal`'s `field_updates` for a proposal whose
   `proposed_item_type` is `"assertion"`; a subsequent `GET` on that proposal reflects the new
   value, and a `history/` snapshot exists — same verification style TASK-013's own AC7 uses for
   its own fields.
8. `edit_proposal` with `proposed_path_segments` in `field_updates` for a non-`assertion`
   proposal raises `UneditableFieldError` → `400` (assuming the assertion-only allow-list form
   from Scope item 4 was chosen) — or is accepted if the broader `_COMMON_EDITABLE_FIELDS` form
   was chosen instead; whichever form is implemented, this criterion is updated to match and the
   choice is stated explicitly in the ticket's own Implementation notes, not left ambiguous.
9. `GET /domains/<domain>/organization-folders?item_type=assertion` on an empty domain returns an
   empty structure, `200`.
10. The same endpoint against a vault with assertions at multiple taxonomy depths returns the
    distinct segment values per depth, correctly excluding `assert-*` id folders from the segment
    lists.
11. `GET .../organization-folders` with a missing or invalid `item_type` returns `400`
    `ValidationError`.
12. `GET .../organization-folders` with a mismatched `domain` in the URL behaves like every other
    route's `_check_domain` guard (same status/error type).

Frontend:

13. `listOrganizationFolders` in `api/review.js` GETs `/domains/<domain>/organization-folders?
    item_type=<type>` and returns the parsed response (mocked-fetch test).
14. `FolderPathBuilder` with `editable={false}` renders the joined segment path as plain text, no
    interactive elements.
15. `FolderPathBuilder` with `editable={true}` renders one clickable segment per entry, each
    opening a dropdown of that depth's existing options plus "+ Créer nouveau...", and a trailing
    "+ Ajouter" button that appends a new segment.
16. Selecting an existing option or confirming "+ Créer nouveau..." calls `onChange` with the
    updated segments array; the trailing "+ Ajouter" button, after naming the new segment, calls
    `onChange` with the array extended by one entry.
17. `ProposalDetail.jsx`'s edit mode seeds `draftPathSegments` from `frontmatter.proposed_path_segments`
    on entry, and Sauvegarder's `editProposal` call includes `proposed_path_segments:
    draftPathSegments` in `field_updates` alongside the existing three fields.
18. `ProposalDetail.jsx` outside edit mode renders the current `proposed_path_segments` read-only,
    including the empty-list case (renders as an empty/placeholder path, no crash).
19. `Validation.jsx`'s `NoteRow` renders each note's `proposed_path_segments` read-only, with no
    dropdown/add-button rendered anywhere on that page (regression check for the "no edit
    affordance on Validation" scope decision).
20. No file under `src/app/extraction/` is modified by this ticket (regression check, mirrors
    TASK-001e's own out-of-scope boundary).

## Testing requirements

- **Backend**: `pytest`, Flask `test_client()` for the new route, `tmp_path`-backed vault
  fixtures at multiple taxonomy depths for the scan logic, covering AC1-12.
- **Frontend**: Vitest + React Testing Library, mocked `fetch`/API modules only, covering AC13-20.
- Project-wide bar: **at least 80% coverage** on every file touched.

## Out of scope

- Entity/event/relationship folder organization — deferred to whenever TASK-005/TASK-012 land and
  adopt ADI-012's layout for those types (see the note added to TASK-005's own ticket).
- Bulk actions (TASK-015) — same GUI-socle boundary as every ticket before this one.
- A folder-creation endpoint independent of `accept_proposal` (see Scope item 5's V1 decision).
- Retroactive relocation of already-canonical files.
- Server-side "nice" segment-name normalization (lowercasing, whitespace-to-hyphen) beyond the
  security-motivated rejection of `/`/`..` — the mockup's client-side `cleanName` convention is a
  frontend nicety this ticket may port but does not require as a backend guarantee.
- Any change to `review.edit_proposal`'s mechanism, `history/` behavior, or
  `EDITABLE_FIELDS_BY_TYPE` beyond the one new entry.
