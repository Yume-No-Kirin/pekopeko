# TASK-014: Folder-Path Organization — Backend API + Frontend Builder (Assertions, V1)

- **Status**: completed

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
  display only, matching TASK-013's precedent. **Superseded 2026-09-05, see "Amendment" below.**
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

## Implementation notes (2026-09-04)

Implemented exactly as scoped, with the design decisions the ticket left open resolved as follows:

- **Segment-value validation location** (Scope item 1 left this open): a single new
  `_validate_path_segments()` helper in `review/storage.py`, called from exactly one site — inside
  `assertion_path()`. Both `write_assertion_file` and `accept_proposal` route through
  `assertion_path`, so this is the one choke point that catches a bad segment (`/` or `..`) before
  any write, without touching `edit_proposal`'s mechanism as the Constraints section required. A
  reviewer can technically save an invalid segment through `edit_proposal` (only key names are
  validated there via `_validate_editable_fields`), but it is caught deterministically the moment
  `accept_proposal` runs — before any file is written and before the Proposal's own status changes.
  Reused `review.errors.ValidationError` (no new exception type); already mapped to `400` via
  `api/app.py`'s `ERROR_STATUS_MAP` — no change needed there, confirming Scope item 6's prediction.
- **`EDITABLE_FIELDS_BY_TYPE` form** (Scope item 4, AC8): the assertion-only form was chosen —
  `"assertion": _COMMON_EDITABLE_FIELDS | {"proposed_path_segments"}` — rebinding only that one
  dict entry to a new set via `|`, leaving `_COMMON_EDITABLE_FIELDS` itself unmutated (it was
  previously the *same object* `"assertion"` pointed at, not a copy — mutating it in place would
  have silently leaked the field into `entity`/`event`/`relationship` too).
- **Folders endpoint response shape** (Scope item 5 left this open): finalized as
  `{"segments_by_depth": [["mythologie", "livres"], ["japonaise"], ...]}` — index `i` is depth `i`
  (0-based, directly under `assertions/`), each inner list deduped and sorted.
  `review/storage.py::scan_organization_folders` walks `<vault_root>/<domain>/assertions/`
  recursively; a directory name matching the `assert-` prefix `_generate_assertion_id` produces is
  treated as an item's own id folder (a leaf, not descended into further); every other name is
  collected as a taxonomy segment at its depth.
- **Frontend `FolderPathBuilder.jsx`**: controlled component (no DOM mutation), ported from the
  mockup's `toggleFolderDropdown`/`selectFolder`/`createNewFolder`/`addFolderSegment` with an inline
  input + "Créer"/"Annuler" buttons in place of `window.prompt()`, per the ticket's own instruction.
  CSS ported verbatim from `pekopeko-proposal-detail.html:531-633` (the reference block —
  `Validation.jsx`'s read-only rendering needs no dropdown/hover states, so `pekopeko-workflow.html`'s
  denser table-cell variant was not used); a new `.folder-dropdown-create-form` block (no mockup
  equivalent, since both mockups use `window.prompt()`) styled after the existing
  `.modal-textarea`/`.filter-select` conventions.
- **`ProposalDetail.jsx`**: `listOrganizationFolders` is fetched only inside `handleEditToggle`
  (once per edit-mode session, per the ticket's own "no over-fetch" rule), not in the mount-time
  `useEffect` alongside the other three fetches. A 5th metadata row ("Dossier proposé") added after
  "Validité". Sauvegarder's `field_updates` gained a 4th key, `proposed_path_segments`.
- **`Validation.jsx`**: `NoteRow` gained a 4th, always-read-only `<td>` (`editable={false}`,
  matching TASK-013's precedent of no edit affordance on this page) between the type badge and
  actions cells; `<thead>` and the two hard-coded `columnCount`/`colSpan={3}` references updated to
  4.
- Code: `src/app/review/storage.py` (`_validate_path_segments`, `assertion_path`,
  `write_assertion_file`, `EDITABLE_FIELDS_BY_TYPE`, `scan_organization_folders`),
  `src/app/review/pipeline.py::accept_proposal`, `src/app/api/routes_review.py` (new
  `GET .../organization-folders` route), `src/app/api/serialization.py`
  (`organization_folders_to_dict`) — no change to `src/app/api/app.py` (confirmed no new error
  mapping was needed). `frontend/src/components/FolderPathBuilder.jsx` (new),
  `frontend/src/api/review.js` (`listOrganizationFolders`), `frontend/src/pages/ProposalDetail.jsx`,
  `frontend/src/pages/Validation.jsx`, `frontend/src/index.css`. No file under `src/app/extraction/`
  touched (AC20).
- Tests: 3 new backend test files' worth of cases added to existing files
  (`src/tests/review/test_storage.py`, `test_pipeline_accept.py`, `test_pipeline_edit.py`,
  `src/tests/api/test_review_routes.py`) plus `frontend/src/components/FolderPathBuilder.test.jsx`
  (new, colocated per this directory's `ProvenanceSection.jsx`/`.test.jsx` precedent),
  `frontend/src/api/review.test.js`, `frontend/src/pages/ProposalDetail.test.jsx`,
  `frontend/src/pages/Validation.test.jsx`. Two pre-existing tests were updated in place as a
  necessary consequence of this ticket, not a silent behavior change: `ProposalDetail.test.jsx`'s
  "TASK-013 AC12" exact-payload assertion now includes the 4th `proposed_path_segments` key (always
  sent, defaulting to `[]`); `Validation.test.jsx`'s "AC3" now expects 4 columns including "Dossier
  proposé" instead of TASK-013-era's "no folder column" expectation.

## Verification record (2026-09-04)

Verified by Claude (same session as implementation — same limitation as every prior ticket in this
project: not a second independent reviewer). Per this project's verification discipline, code was
copied to an isolated location outside the repo
(`%LOCALAPPDATA%\Temp\claude\...\scratchpad\task014_verify\`): backend `src/` copied fresh (no
`__pycache__`), frontend `frontend/src/` plus `.env`/`.env.test`/config files copied fresh with
`node_modules` linked via an NTFS junction rather than reinstalled (same approach as TASK-013's own
verification) — every check below was re-run there independently, not just trusted from the
in-repo run.

- Backend, isolated copy (per-package `pytest`, since this repo's `src/tests/` has a pre-existing,
  documented cross-directory `_helpers.py` collection collision unrelated to this ticket):
  `src/tests/review` 115/115 pass, 100% coverage on every touched file
  (`storage.py`/`pipeline.py`/`errors.py`/`frontmatter.py`); `src/tests/api` 108/108 pass, 100%
  coverage on `routes_review.py`/`serialization.py`; `src/tests/extraction` 65/65 pass (untouched,
  regression check for AC20); `src/tests/config` 39/39 pass (untouched). `src/tests/ingestion` has
  2 pre-existing failures (`test_comprehensive.py::test_acceptance_criteria_compliance`,
  `test_pipeline.py::test_import_isolation`) confirmed via `git stash` to be present identically on
  the pre-TASK-014 code — not a regression.
- Frontend, isolated copy: `npx vitest run --coverage` 79/79 pass. Global coverage 97.94% stmts /
  89.29% branch / 81.53% funcs / 97.94% lines — passes the project's configured 80% threshold on
  all four metrics (`vite.config.js`'s `coverage.thresholds`). `review.js` 100%.
  `FolderPathBuilder.jsx` has 7 dedicated tests but isn't counted toward the threshold —
  `src/components/**` is outside this project's coverage `include` list (`src/api/**`,
  `src/pages/**` only), a pre-existing config choice unrelated to this ticket.
- `git status --porcelain -- src/app/extraction/ src/tests/extraction/` returns empty (AC20).
- Manual end-to-end reproduction, actually executed (not narrated) in the isolated copy, two steps:
  1. **Pipeline level**: built a real PROPOSED assertion proposal on disk with
     `proposed_path_segments: ["mythologie", "japonaise"]`, called `pipeline.accept_proposal(...)`
     for real. Result: `assertion_path` =
     `manual_vault/FICTION/assertions/mythologie/japonaise/assert-5cba7aed-.../assert-5cba7aed-....md`,
     `.exists()` = `True`, `scan_organization_folders(vault, "FICTION")` =
     `[['mythologie'], ['japonaise']]`. Frontmatter inspected by eye — all fields correct, body
     preserved verbatim.
  2. **HTTP level**: built a real Flask app (`create_app`) against the same scratch vault, issued
     real requests via `app.test_client()`: `GET .../organization-folders?item_type=assertion` →
     `200 {'segments_by_depth': [['mythologie'], ['japonaise']]}`; `GET .../organization-folders`
     (no `item_type`) → `400 {'error': {'type': 'ValidationError', ...}}`.

Acceptance criteria checked one by one:

- `[PASS]` AC1-2 (`assertion_path` no-segments regression / with-segments construction) —
  `test_assertion_path_no_segments_matches_current_behavior`,
  `test_assertion_path_with_segments_inserts_between_assertions_and_id`.
- `[PASS]` AC3 (`write_assertion_file` writes to the segmented path, readable back) — exercised
  transitively via `test_accept_proposal_writes_segmented_path_when_proposed_path_segments_present`
  and confirmed directly in the manual repro (step 1 above).
- `[PASS]` AC4-5 (`accept_proposal` writes segmented/plain path present/absent) —
  `test_accept_proposal_writes_segmented_path_when_proposed_path_segments_present`,
  `test_accept_proposal_writes_plain_path_when_proposed_path_segments_absent`, plus every
  pre-existing `test_pipeline_accept.py` test (all still pass, confirming no regression for
  pre-TASK-001e proposals lacking the field).
- `[PASS]` AC6 (invalid segment rejected before any write) —
  `test_validate_path_segments_rejects_slash`/`_rejects_dotdot` (unit) and
  `test_accept_proposal_rejects_invalid_path_segments_before_any_write` (integration: proposal file
  byte-identical after the raise, `assertions/` empty or absent).
- `[PASS]` AC7 (`edit_proposal` accepts the field for assertion, `history/` snapshot exists) —
  `test_edit_proposal_field_update_assertion_proposed_path_segments`.
- `[PASS]` AC8 (uneditable for non-assertion; assertion-only form documented above) —
  `test_edit_proposal_proposed_path_segments_uneditable_for_non_assertion`,
  `test_editable_fields_by_type_assertion_scoped_only`.
- `[PASS]` AC9-10 (folders endpoint empty domain / multi-depth scan) —
  `test_get_organization_folders_empty_domain_returns_empty_structure`,
  `test_get_organization_folders_multi_depth_scan` (API level) plus
  `test_scan_organization_folders_empty_domain`,
  `test_scan_organization_folders_multi_depth_excludes_assert_prefix` (unit level), confirmed live
  in the manual repro's step 2.
- `[PASS]` AC11 (missing/invalid `item_type` → 400) —
  `test_get_organization_folders_missing_item_type_returns_400`,
  `test_get_organization_folders_invalid_item_type_returns_400`, confirmed live in the manual repro.
- `[PASS]` AC12 (domain mismatch matches `_check_domain` convention) —
  `test_get_organization_folders_invalid_domain_returns_400`.
- `[PASS]` AC13 (`listOrganizationFolders` GET shape) — `review.test.js` "TASK-014 AC13".
- `[PASS]` AC14 (read-only renders plain text, no interactive elements, incl. empty case) —
  `FolderPathBuilder.test.jsx` "AC14" (2 tests).
- `[PASS]` AC15 (editable renders segments + dropdown + options + "+ Créer nouveau..." + "+
  Ajouter") — `FolderPathBuilder.test.jsx` "AC15" (2 tests).
- `[PASS]` AC16 (selecting/creating/adding each call `onChange` correctly) —
  `FolderPathBuilder.test.jsx` "AC16" (3 tests).
- `[PASS]` AC17 (edit mode seeds `draftPathSegments` + fetches folders; save includes the field) —
  `ProposalDetail.test.jsx` "TASK-014 AC17" (2 tests); pre-existing "TASK-013 AC12" payload
  assertion updated in place to match (see Implementation notes).
- `[PASS]` AC18 (read-only rendering outside edit mode, incl. empty case) —
  `ProposalDetail.test.jsx` "TASK-014 AC18" (2 tests).
- `[PASS]` AC19 (`Validation.jsx` read-only column, no edit affordance anywhere on the page) —
  **superseded 2026-09-05, see "Amendment" below** — `Validation.test.jsx` "TASK-014 AC19"
  originally verified this; that test was rewritten in place to assert the new editable
  behavior instead.
- `[PASS]` AC20 (no file under `src/app/extraction/` modified) — confirmed via `git status
  --porcelain`, and `src/tests/extraction` 65/65 unchanged.

## Amendment (2026-09-05): inline editing in the Validation table, matching the mockup

Cleo asked, referencing the mockup directly, for the folder path to be editable inline in
`Validation.jsx`'s table rather than only in `ProposalDetail.jsx`'s edit mode — reversing this
ticket's own AC19/Scope item 10 decision ("no inline edit affordance on Validation.jsx, matching
TASK-013's precedent"). Checking `specs/ux-design/pekopeko-workflow.html` directly confirmed the
mockup's own `folder-path-builder` markup is always interactive (`toggleFolderDropdown`/
`selectFolder`/`createNewFolder` wired on every row, no separate read-only/edit-mode toggle for
this column) — the original TASK-014 read-only choice was a deliberate MVP narrowing at the time,
not a misreading of the mockup, but Cleo has now asked for parity with it.

What changed, additively:

- `Validation.jsx`: `NoteRow`'s `FolderPathBuilder` is now `editable={true}` (was `editable={false}`
  with a no-op `onChange`). A new `onPathChange(domain, id, segments)` handler applies the change
  optimistically to local `groups` state, then calls `editProposal(domain, id, REVIEWER_ID,
  { fieldUpdates: { proposed_path_segments: segments } })` (no `body`, matching `edit_proposal`'s
  existing `body=None` "leave unchanged" contract) - a failed call reverts the optimistic update
  and surfaces `actionError`, same pattern already used by `handleAccept`/`handleRejectConfirm`.
  There is no per-row Save/Cancel step, matching the mockup: each dropdown selection or "+ Créer
  nouveau..." confirmation calls `editProposal` immediately, so each one also creates its own
  `history/` version (existing `edit_proposal` behavior, unchanged) - a note edited segment-by-
  segment across several clicks accumulates one history snapshot per click, not one for the whole
  session. Not fixed here - flagged for whoever revisits this if it becomes a real cost.
- New `fetchFolderOptionsByDomain(domains)`: one `listOrganizationFolders(domain, "assertion")`
  call per domain visible in the current filter, fetched alongside `fetchGroups` in the same
  effect; a failed fetch for one domain degrades to no suggested options for that domain rather
  than blocking the table (same non-blocking-satellite posture as the rest of this fetch).
  `NoteRow` gains a `folderOptions` prop sourced from this map.
- `proposal_status` transitions `PROPOSED` → `EDITED` on the first inline path edit, same as any
  other `edit_proposal` call - already handled without change, since `fetchGroups` already fetches
  both `PROPOSED` and `EDITED` (TASK-013's own fan-out), so an edited row stays visible in the
  table under the same filters.

**Tests**: `Validation.test.jsx`'s "TASK-014 AC19" test (asserted plain-text/no-dropdown) rewritten
in place to assert segment buttons + a "+ Ajouter" button are present; `makeFetchMock` gains
`organizationFoldersByDomain` and `editShouldFail` (mirroring `ProposalDetail.test.jsx`'s existing
pattern) plus handlers for `GET .../organization-folders` and `POST .../edit`. Two new tests: one
drives a real click → dropdown-option-click interaction and asserts `editProposal` was called with
the correct `field_updates.proposed_path_segments` and that the row updates without a refetch; one
asserts a failed edit reverts the row and shows `actionError`. `npx vite build` and `npx vitest run
--coverage` both pass: 81/81 frontend tests, 97.64% lines on `Validation.jsx` (no regression on any
other file).

**Verified against the real backend**, not only mocked: called the actual running Flask API's
`POST /domains/FICTION/proposals/<id>/edit` (the exact call `editProposal` makes) against a real
Proposal already in the vault, confirmed via a follow-up `GET` that `proposed_path_segments` was
updated and `proposal_status` became `EDITED`, then reverted the test edit back to its original
value via the same endpoint. A literal browser screenshot was not obtained - neither `chromium-cli`
nor a local Playwright install was available in this environment, and installing one wasn't asked
for; this is the same disclosed limitation already present in every prior frontend ticket's own
Verification record ("pas de test de fumée contre une vraie instance Flask/vault" - here a real
Flask+vault smoke test *was* done, at the API level, just not with an actual rendered browser).

## Amendment (2026-09-05): mockup fidelity fix + drag-to-reorder segments

Cleo pointed out, from a screenshot of the running `Validation.jsx` table, that the "Dossier
proposé" column's visual design didn't match `pekopeko-workflow.html` closely enough, and asked
for segments to be reorderable by long-press-and-drag on both editable screens
(`Validation.jsx` and `ProposalDetail.jsx`'s edit mode).

**Root cause of the visual gap**: the original TASK-014 implementation note above already flags it
- `FolderPathBuilder`'s CSS was ported only from `pekopeko-proposal-detail.html:531-633`'s
borderless flavor, a choice made when `Validation.jsx`'s builder was still read-only per this
ticket's own original Scope item 10. The 2026-09-05 "inline editing" amendment above made
`Validation.jsx`'s builder fully interactive but never revisited the CSS, so the table's "Dossier
proposé" column kept rendering with the wrong (proposal-detail) skin, and `.folder-cell` (the `<td>`
class `Validation.jsx` already uses) had no CSS backing it at all.

**Drag-to-reorder** has no mockup equivalent - both mockups only ever replace a segment's value
(dropdown) or append one (`+ Ajouter`), never reorder. This is a new, additive interaction
requested directly, not a mockup-fidelity gap.

What changed:

- `frontend/src/index.css`: added a `.folder-cell`-scoped block (ported from
  `pekopeko-workflow.html:391-505`) - bordered container, monospace font, denser grey pill
  buttons - that overrides the default proposal-detail skin only inside `Validation.jsx`'s table
  cell context. `ProposalDetail.jsx`'s `.metadata-value` context is untouched (it already matched
  its own mockup). Also added `.folder-segment.dragging .folder-segment-btn` (a distinct blue
  tint + `cursor: grabbing`, the "closed fist" cursor - refined the same day per Cleo's direct
  follow-up request, see below) and `touch-action: none` on `.folder-segment-btn` for the drag
  gesture.
- `frontend/src/components/FolderPathBuilder.jsx`: added Pointer Events-based drag-to-reorder,
  active only when `editable={true}` (so both `Validation.jsx`'s always-editable row and
  `ProposalDetail.jsx`'s edit mode get it identically, for free). Gesture: pointer-down starts a
  400ms timer; if the pointer moves more than ~6px before it fires, it's cancelled and the
  eventual click behaves exactly as before (opens the segment's dropdown). As soon as the timer
  fires - i.e. the moment the long press is recognized, before the pointer has necessarily moved
  at all - the segment gets the tinted/grabbing-cursor visual cue, so the reviewer can see the
  segment is now liftable; if the pointer then actually moves, it is reordered live in local
  component state (via each segment's `getBoundingClientRect()`, no `onChange` per intermediate
  swap) and `onChange` is called exactly once, on release, with the settled order - mirroring
  this component's existing "one `onChange` per discrete user action" pattern rather than firing
  one `editProposal` call per pixel of drag. A held-then-released-without-moving press clears the
  visual cue and is treated as an ordinary click (dropdown still opens), matching the forgiving
  long-press-then-drag pattern used by other reorderable-list UIs.
- No backend change: `proposed_path_segments` was already a plain ordered array end-to-end, so a
  reordered array flows through the existing `editProposal`/`field_updates` path unchanged.

**Implementation note**: the first working version of the drag logic had a real bug caught by its
own tests, not just a test artifact - the swap computation read `info.position` (a mutable ref
field) from inside a `setOrder` functional updater, but `info.position` gets reassigned
synchronously right after `setOrder` is called, before React actually invokes that updater during
its later render pass; the updater was therefore reading the *destination* index as if it were the
*source* index, silently reconstructing the original (unchanged) order. Fixed by snapshotting the
source position into a local `const` before the mutation. Caught immediately by the new
drag-reorder test asserting the exact resulting array, not just that `onChange` was called.

**Tests**: `frontend/src/components/FolderPathBuilder.test.jsx` gained a `describe` block with
four cases: a quick press-and-release still opens the dropdown (regression on existing AC15), a
long press held still (no drag) gets the `dragging` class (tint + grabbing cursor) as soon as the
timer fires and loses it on release without triggering a reorder, a long-press-then-drag past
another segment calls `onChange` exactly once with the correctly reordered array and never opens
a dropdown, and a press that moves before the long-press timer fires cancels the drag and behaves
like a normal click. jsdom (25.0.1, this project's pinned version) has no `PointerEvent`
constructor at all (https://github.com/jsdom/jsdom/issues/2527) - `@testing-library/dom`'s
`fireEvent.pointerDown`/`pointerMove`/`pointerUp` silently fall back to a plain `Event` and drop
`clientX`/`clientY`/`pointerId`, so the new tests build the event manually (`new Event(type, {...});
Object.assign(event, {clientX, clientY, pointerId})`) and dispatch it via the lower-level
`fireEvent(el, event)` instead. The armed-highlight test also needed an explicit `act()` around
`vi.advanceTimersByTime(...)`, since the timer callback calls `setState` outside of a
React-managed event and nothing else in that test flushes it before the assertion (unlike the
other drag tests, which assert only after a further `fireEvent` call, whose own `act()` wrapper
flushes it incidentally).

**Verification**: `npx vitest run --coverage` in `frontend/` - 85/85 tests pass (11 in
`FolderPathBuilder.test.jsx`, up from 7), coverage unchanged/above the 80% threshold on every
touched file. `npx vite build` succeeds. Manual verification: the Flask backend and Vite dev
server were both started locally against the real vault
(`PEKOPEKO_VAULT_ROOT`/`PEKOPEKO_API_KEY` from `.pekopeko-local.env`) and confirmed reachable
(backend responds to an authenticated request, frontend serves `200`); a rendered-browser
screenshot comparison against the mockup, and a manual long-press-drag trial, were left for Cleo
to check directly in that already-running instance - same disclosed browser-automation limitation
as the 2026-09-05 amendment above (no `chromium-cli`/Playwright available in this environment).
