# TASK-009a: GUI Ingestion Trigger — Upload, Domain, Optional Context

- **Status**: completed

## Objective

Close the gap named by TASK-009's own Out of scope section: the "+ Nouvelle ingestion" button
shown in `specs/ux-design/pekopeko-ingestion.html` is currently `onclick="alert('Nouvelle ingestion
à implémenter')")` — a stub. TASK-009 (`completed`) deliberately left it unimplemented ("no endpoint
exists to start an ingestion from an arbitrary user-supplied path… no satellite proposed for it").
The endpoint it needed now exists (`POST /domains/<domain>/ingestions`, TASK-007, `completed`), and
`specs/tasks/BACKLOG-CLAUDE-V2.md` §3 already reserves this ticket's ID (TASK-009a, satellite of
TASK-009) for exactly this gap — but only as a two-line sketch, not a full ticket, and that sketch
predates the two requirements Cleo added when this ticket was actually written (2026-09-07): a real
file **upload** (not a "local path" text field) and an optional **context** field with
autocompletion.

**Why "upload" is new backend scope, not just frontend wiring.** The frontend is an ordinary web
app — Vite/React in a browser, talking to Flask on `127.0.0.1` (ADI-009/ADI-010) — not an Electron
shell. A browser cannot expose the absolute filesystem path of a file chosen via
`<input type="file">`. `POST /domains/<domain>/ingestions` (`src/app/api/routes_ingestion.py:30`)
only accepts a JSON `{"source_path": "..."}` already readable by the API process. A real "upload"
(the user picks a file, its bytes are sent over HTTP) is therefore a genuinely new backend
capability — this ticket's main piece of new scope, not a UI-only change.

**Why "context" needs a blocking dependency.** The `context` field (ADI-016, "Context/Universe as a
first-class field") has **no backend support at all today**: both halves of its implementation —
TASK-014a (storage: makes `context` a real, editable, path-affecting field) and TASK-014b (automatic
derivation from source folder / LLM) — are still `backlog`. TASK-014a's own "V1 scope decisions"
explicitly named the exact feature Cleo is asking for here as deferred: *"No dedicated
`GET .../organization-folders`-style endpoint for `context` values... a suggestions dropdown can be
added later if reviewers find themselves retyping values, without this ticket blocking on it."* This
ticket is that later addition. Decided with Cleo (2026-09-07): this ticket is written now, but
**blocks on TASK-014a** for its context half — without TASK-014a, a `context` value set through this
ticket's form has nowhere to be consumed (`accept_proposal` doesn't read `context` at all yet, and
`edit_proposal` would reject it as an unrecognized field).

**Real upload target, decided with Cleo (2026-09-07)**: uploaded bytes are written into
`<vault_root>/<domain>/_inbox/` — reusing the existing ADI-013 convention — rather than a separate
non-canonical staging folder.

**Explicitly not the same scope as `BACKLOG-CLAUDE-V2.md`'s TASK-009a sketch.** That sketch paired a
local-path field with a second, URL-based entry gated on TASK-016. Per Cleo's own framing today
("uploader un .md, plus tard d'autres formats, voir url"), this ticket covers **only** the `.md`
upload path. The URL entry is out of scope here (see Out of scope) — a future satellite once TASK-016
lands, not silently dropped.

## Binding context (references, not duplicated here)

- **ADI-013** (`specs/decisions/ADI-013-automatic-folder-ingestion.md`, Accepted): defines the
  per-domain `_inbox/` convention this ticket's upload target reuses directly (as a literal folder
  name, not through `FolderWatchConfig` — see Dependencies for why).
- **ADI-016** (`specs/decisions/ADI-016-context-universe-first-class-field.md`, Accepted): the
  `context` field this ticket's form collects a value for. `context` is always `Optional[str]`,
  never forced non-empty — this ticket's form must allow submitting with no context at all.
- **TASK-014a** (`specs/tasks/backlog/TASK-014a-context-field-storage-and-scoped-scan.md`, `backlog`,
  **blocking**): makes `context` a recognized field in `_COMMON_EDITABLE_FIELDS` and in
  `accept_proposal`'s four type branches. Read it in full — this ticket's context half only becomes
  meaningful once it lands.
- `src/app/api/routes_ingestion.py:30-52` (`start_ingestion`): the exact dispatch shape
  (`create_task_state`/`update_task_state`/`run_in_background(ingest_source, ...)`) this ticket's new
  upload route reuses, swapping only where the source file comes from.
- `src/app/ingestion/pipeline.py:36` (`ingest_source`): unchanged by this ticket — the upload route
  calls it exactly as `start_ingestion` does, on a path under `_inbox/` instead of an arbitrary
  caller-supplied path.
- `src/app/review/pipeline.py:239-335` (`accept_proposal`) and its file-persistence behavior: a
  Proposal file is never deleted or moved out of `proposals/<id>/<id>.md` on acceptance — only its
  `proposal_status` field changes to `ACCEPTED` (verified by reading the function in full before
  writing this ticket). This is what makes scanning `proposals/*/*.md` for `context` values a
  complete, non-lossy source for the new suggestions endpoint (see Scope §5).
- `src/app/ingestion/storage.py:113-143` (`scan_proposed_path_segments`): the existing precedent for
  scanning `proposals/*/*.md` frontmatter for a distinct-values list. This ticket's own
  `scan_existing_contexts` (Scope §5) follows the same shape but does **not** filter by
  `proposed_item_type` (context is cross-type, ADI-016) or by `proposal_status` (a context value
  used by an already-`ACCEPTED` or `REJECTED` proposal is still a valid suggestion).
- `frontend/src/api/client.js` (`request`, `get`, `post`): every outgoing request goes through this
  module (TASK-008/009 convention) and today always JSON-serializes its body — this ticket adds the
  first multipart request the frontend makes.
- `frontend/src/components/RejectReasonModal.jsx`: the exact modal pattern (`.modal-overlay`/
  `.modal`/`.modal-header`/`.modal-body`/`.modal-actions`, already styled) this ticket's new modal
  component follows, rather than inventing new modal markup/CSS.
- `frontend/src/pages/IngestionLogs.jsx:192-204` (`header-actions`): today contains only the
  "↻ Rafraîchir" button — the "+ Nouvelle ingestion" button from the mockup does not exist in the
  real screen yet and is added here.
- `frontend/src/api/domains.js` (`DOMAINS`) and `src/app/api/domains.py` (`VALID_DOMAINS`): the fixed
  5-domain list (`PERSONAL`, `FICTION`, `LEARNING`, `RESEARCH`, `PUBLISHING`) this ticket's domain
  dropdown reuses as-is — no new domain logic.
- TASK-006/TASK-013 (`completed`): `edit_proposal` / `POST .../proposals/<id>/edit`, reused as-is by
  this ticket's frontend to apply a user-supplied `context` to each proposal an ingestion produces
  (see Scope §4) — no backend change to this mechanism beyond what TASK-014a already brings.
- TASK-001d (`completed`, INV-020): content-hash-based duplicate detection — cited in Constraints as
  why this ticket does not need to coordinate with TASK-001f's watcher (still `backlog`).

## Scope

### Backend

1. **New route** `POST /domains/<domain>/ingestions/upload` in `src/app/api/routes_ingestion.py`
   (multipart/form-data, field `file`; no `context` field server-side — see §4 for why `context` is
   handled entirely by the frontend, after ingestion completes). Validates `domain` against
   `VALID_DOMAINS` (`400` otherwise, same convention as `start_ingestion`) and that a file was sent
   with a `.md` extension (case-insensitive; `400 ValidationError` otherwise, nothing written to
   disk). On success:
   - Mints `task_id = f"ingest-{uuid.uuid4()}"` (same shape as `start_ingestion`).
   - Sanitizes the uploaded filename with `werkzeug.utils.secure_filename` (already a Flask
     dependency, no new requirement) and writes the file's bytes to
     `<vault_root>/<domain>/_inbox/<task_id>-<secure_filename>` (creating `_inbox/` if missing) —
     the `task_id` prefix guarantees uniqueness without needing a separate collision check.
   - Calls `create_task_state`/`update_task_state`/`run_in_background(ingest_source, vault_root,
     domain, <written_path>, provider, state_dir, task_id)` — identical sequence to
     `start_ingestion`, only the file's origin differs.
   - Returns `202 {"task_id": ..., "status": "pending"}` — same response shape as `start_ingestion`.
2. **New route** `GET /domains/<domain>/contexts` in `src/app/api/routes_review.py` (same blueprint
   as the existing `GET .../organization-folders`, no new blueprint). Validates `domain`, calls the
   new `scan_existing_contexts` (§5), returns `{"contexts": [...]}` (sorted, distinct, non-null
   values).
3. **New function** `review/storage.py::scan_existing_contexts(vault_root: Path, domain: str) ->
   list[str]`: iterates `<vault_root>/<domain>/proposals/*/*.md`, best-effort frontmatter read
   (reusing the existing `_read_frontmatter`-style tolerance for a malformed file — one bad Proposal
   must not break the scan), collects distinct non-null `context` values across **every**
   `proposal_status` and every `proposed_item_type` (unlike `scan_proposed_path_segments`, no status
   or type filter — see Objective for why). Returns `[]` if `proposals/` doesn't exist yet.
4. **No change** to `ingest_source`, `ExtractedAssertion`, any provider, `TaskState`, or
   `accept_proposal` beyond what TASK-014a itself brings. A user-supplied `context` value is applied
   to the ingestion's resulting Proposals **after the fact**, by the frontend, via the existing
   `edit_proposal` endpoint (TASK-006/013) — see Frontend §7. This avoids threading a new parameter
   through `ingest_source`/the provider contract (that surface belongs to TASK-014b, not this
   ticket) and avoids any conflict with TASK-014b's own future design (`ExtractedAssertion.context`,
   per-item, provider-decided) — a human-supplied value applied via `edit_proposal` composes safely
   with whatever TASK-014b later derives automatically, whichever lands first.

### Frontend

5. `frontend/src/api/client.js`: new exported function (e.g. `postForm(path, formData)`) that issues
   a `fetch` with a `FormData` body (browser sets the multipart `Content-Type` boundary
   automatically — no explicit header), still attaching `X-API-Key` and reusing the existing
   `ApiError` parsing from `request`'s non-2xx branch. `request`/`get`/`post` are unchanged.
6. `frontend/src/api/tasks.js`: two new exports —
   - `startIngestionUpload(domain, file)` → `postForm(/domains/${domain}/ingestions/upload, ...)`.
     This is the wrapper TASK-016 already assumed would exist ("alongside the existing
     `startIngestion`") but that, in fact, no ticket had written yet.
   - `getIngestion(domain, taskId)` → `get(/domains/${domain}/ingestions/${taskId})` — a single-task
     GET wrapper; today only `listIngestions`/`listExtractions` exist, nothing wraps the existing
     per-task `GET` route needed for polling (§7).
7. `frontend/src/api/review.js`: new export `listContexts(domain)` →
   `get(/domains/${domain}/contexts)`.
8. **New component** `frontend/src/components/NewIngestionModal.jsx` (+ `.test.jsx`), structurally
   modeled on `RejectReasonModal.jsx` (same `.modal-overlay`/`.modal`/`.modal-header`/`.modal-body`/
   `.modal-actions` classes, no new CSS):
   - File field (`<input type="file" accept=".md">`); submission is disabled with no file selected;
     a client-side check on `file.name` rejects non-`.md` selections with an inline message
     (defense in depth — the server is the authority, per §1).
   - Domain `<select>`, options from `DOMAINS` (`frontend/src/api/domains.js`), required.
   - Context `<input type="text">` (optional, free text) paired with a native `<datalist>` populated
     from `listContexts(domain)` — refetched whenever the selected domain changes. No new frontend
     dependency for autocompletion.
   - On submit: calls `startIngestionUpload(domain, file)`. On success, closes the modal and
     surfaces the returned `task_id` to the caller (parent decides what to show — TASK-009's own
     screen already displays new tasks on its next refresh).
9. `frontend/src/pages/IngestionLogs.jsx`: adds a "+ Nouvelle ingestion" button to `header-actions`
   (currently only "↻ Rafraîchir"), opening `NewIngestionModal`. On the modal's successful submit:
   - Triggers a refresh (reuse the existing `refreshKey` mechanism) so the new task appears in the
     table.
   - If a non-empty `context` was entered, starts polling `getIngestion(domain, taskId)` (e.g. every
     2s, capped at ~60 attempts) until `status` is `completed` or `failed`; on `completed`, calls
     `editProposal(domain, proposalId, REVIEWER_ID, { fieldUpdates: { context } })` (existing
     TASK-006/013 endpoint) for every id in the task's `proposal_ids`, in parallel (`Promise.all`).
     `REVIEWER_ID` reuses the existing module-level constant pattern already present in
     `Validation.jsx`/`ProposalDetail.jsx` (`import.meta.env.VITE_REVIEWER_ID || "cleo"`).
   - Polling is cancelled if the component unmounts (navigation away) before completion, and gives
     up silently after the attempt cap — the ingestion itself already succeeded either way; only the
     retroactive `context` application is skipped (see V1 scope decisions).

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **`_inbox` is a hardcoded literal here, not read from `FolderWatchConfig`.** That config type is
  introduced by TASK-001f (`backlog`), a background watcher this ticket has nothing to do with —
  taking a dependency on it would couple an explicit, synchronous button to an unrelated poller.
  Known, accepted drift: if TASK-001f later ships with a non-default `inbox_dirname`, this button's
  upload target and the watcher's scanned folder would diverge until a small follow-up aligns them
  — same "named limitation, not preemptively engineered around" posture ADI-014/015 already used.
- **No move to `processed/`.** This ticket's upload flow dispatches `ingest_source` directly and
  never touches a `processed/` subfolder (that concept belongs to TASK-001f). If TASK-001f is later
  enabled and its watcher re-scans `_inbox/` before this ticket's own ingestion has, in principle,
  moved anything (it moves nothing), the existing content-hash duplicate detection (TASK-001d,
  INV-020, `completed`) already prevents a second, redundant ingestion of the same bytes — no new
  mechanism needed here.
- **`context` is applied after ingestion completes, not at ingestion time.** A value typed into the
  form only reaches the resulting Proposals via a post-completion `edit_proposal` call from the
  frontend (§7). If the browser tab/page is closed before polling finishes, the context is **not**
  retroactively applied — recoverable manually via the already-existing context editor in
  `ProposalDetail.jsx` (once TASK-014a ships it). Named here deliberately, not hidden.
  This ticket is the client-side "someone actually calls it" fix for the dead-code gap TASK-016
  itself flagged (`startUrlIngestion` with no caller) — applied here to `startIngestionUpload`, which
  this ticket both adds and wires into `IngestionLogs.jsx`, unlike TASK-016's own wrapper.
- **No file-size cap.** Flask's default has no `MAX_CONTENT_LENGTH`; this ticket does not add one.
  Named as a known gap, not silently ignored — acceptable for a single-user local tool (ADI-010's
  security posture), not addressed here.
- **URL-based ingestion entry is out of scope** (see Out of scope) — deferred to a future satellite
  once TASK-016 lands, per Cleo's explicit "plus tard" framing for non-`.md` sources.

## Requirements

- **Backend**: Python/Flask only, no new dependency (`werkzeug.utils.secure_filename` ships with
  Flask already). Same testing discipline as prior tickets: `pytest`, `tmp_path`-backed vault
  fixtures, Flask test client's multipart support (`data={"file": (io.BytesIO(...), "name.md")}`)
  for the new route.
- **Frontend**: React function components, existing `frontend/src/api/*.js` wrapper style, no direct
  `fetch()` outside `client.js`, no new frontend dependency (native `<datalist>` for
  autocompletion). Vitest + React Testing Library, `fetch` fully mocked — no real network calls, no
  dependency on a running Flask instance, no real timers for the polling logic (fake timers).

## Constraints

- No change to `start_ingestion`'s existing JSON contract, to `ingest_source`'s public signature, to
  `ExtractedAssertion`, or to any provider interface.
- No new Flask blueprint (both new routes join existing blueprints — `ingestion_bp`, `review_bp`).
- No dependency on TASK-001f or TASK-014b (see Objective/V1 scope decisions for why, and what safety
  net makes that safe: TASK-001d/INV-020).
- The context suggestions endpoint (`scan_existing_contexts`) must not scan canonical
  (`assertions/`/`entities/`/`events/`/`relationships/`) folders — TASK-014a's path shape (optional
  `context` segment followed by taxonomy segments) makes a folder-name scan structurally ambiguous;
  `proposals/` frontmatter is the only unambiguous source.
- `context` remains `Optional[str]` throughout — submitting the form with an empty context field is
  a fully valid, common case (ADI-016: never forced non-empty).

## Files/modules concerned

- **Backend**: `src/app/api/routes_ingestion.py` (new `upload_ingestion` route), `src/app/api/
  routes_review.py` (new `list_contexts` route), `src/app/review/storage.py` (new
  `scan_existing_contexts`). New/updated tests in `src/tests/api/` (upload route: valid `.md`,
  non-`.md` rejection, invalid domain, file written under `_inbox/<domain>/`, task dispatched;
  contexts route: empty vault → `[]`, distinct values across statuses/types) and `src/tests/review/`
  (`scan_existing_contexts` unit tests, malformed-frontmatter tolerance).
- **Frontend**: `frontend/src/api/client.js` (`postForm`), `frontend/src/api/tasks.js`
  (`startIngestionUpload`, `getIngestion`), `frontend/src/api/review.js` (`listContexts`), new
  `frontend/src/components/NewIngestionModal.jsx` + `.test.jsx`, `frontend/src/pages/
  IngestionLogs.jsx` + `.test.jsx` (button wiring, refresh-on-success, polling + context
  application, polling cancellation on unmount).

## Dependencies

TASK-007 (`completed`, dispatch shape reused as-is), TASK-009 (`completed`, the screen this button is
added to), TASK-006/TASK-013 (`completed`, `edit_proposal`/its HTTP route, reused unmodified),
TASK-001d (`completed`, INV-020 — cited for why no coordination with TASK-001f is needed).

**Blocking: TASK-014a** (`backlog`) — `context` must be a recognized field in
`_COMMON_EDITABLE_FIELDS`/`accept_proposal` before this ticket's context half has any real effect
(the upload+domain half is independently implementable and useful without it, but the two are
written as one ticket since the mockup's single button covers both). This ticket's backend/frontend
code can be written and tested against a mocked `edit_proposal` response either way, but end-to-end
verification of the context half requires TASK-014a to have landed first.

Explicitly independent of TASK-001f and TASK-014b (see V1 scope decisions for the reasoning and the
existing invariant, INV-020, that makes this safe).

## Acceptance criteria

Backend:

1. `POST /domains/<domain>/ingestions/upload` with a valid `.md` file returns `202
   {"task_id": ..., "status": "pending"}`, the file exists under `_inbox/<domain>/`, and the
   returned `task_id` matches a dispatched `ingest_source` call (via a fake `run_in_background`).
2. The same call with a non-`.md` filename returns `400`, and nothing is written to disk.
3. The same call with no `file` part returns `400`.
4. An invalid `domain` returns `400` before any file is written.
5. Two uploads with the same original filename to the same domain both succeed and produce two
   distinct files under `_inbox/<domain>/` (uniqueness via the `task_id` prefix).
6. `GET /domains/<domain>/contexts` on a domain with no `proposals/` yet returns `{"contexts": []}`.
7. `GET /domains/<domain>/contexts` returns the distinct, non-null `context` values across Proposals
   of every `proposal_status` (`PROPOSED`/`EDITED`/`ACCEPTED`/`REJECTED`) and every
   `proposed_item_type`, sorted, with no duplicates.
8. A malformed Proposal file (bad YAML frontmatter) is skipped by `scan_existing_contexts` without
   raising — consistent with `scan_proposed_path_segments`'s existing tolerance.
9. `ingest_source`'s public signature is unchanged (regression check by direct comparison, same
   convention as every prior satellite).

Frontend:

10. `NewIngestionModal` disables submission with no file selected; selecting a non-`.md` file shows
    an inline error and does not call `startIngestionUpload`.
11. Selecting a domain fetches and renders that domain's context suggestions via `listContexts`;
    changing the domain re-fetches for the new domain.
12. Submitting with a file and a domain (no context) calls `startIngestionUpload(domain, file)`
    exactly once; on success the modal closes and the ingestion list refreshes.
13. Submitting with a non-empty context: after `startIngestionUpload` resolves, `getIngestion` is
    polled (mocked timers) until a `completed` status is returned, then `editProposal` is called
    once per `proposal_id` in the result with `field_updates: { context }`.
14. If `getIngestion` never reaches `completed`/`failed` within the attempt cap, polling stops and no
    error is shown to the user (silent give-up, per V1 scope decisions).
15. Unmounting the component (e.g. simulated navigation) while polling is in progress stops further
    `getIngestion` calls.
16. The "+ Nouvelle ingestion" button and its modal exist only on `IngestionLogs.jsx` — no other
    existing screen's tests regress.

## Testing requirements

`pytest` (backend) / Vitest + React Testing Library (frontend), covering AC1-16. Project-wide bar:
at least 80% coverage on every file touched.

## Out of scope

- URL-based ingestion entry (the second form field sketched in `BACKLOG-CLAUDE-V2.md` §3, gated on
  TASK-016) — deferred to a future satellite once TASK-016 lands, per Cleo's explicit V1 framing.
- Any non-`.md` file format (PDF, plain text, etc. — TASK-017's scope).
- Populating `context` automatically from anything (folder, LLM) — TASK-014b's entire scope; this
  ticket only carries a human-typed value.
- A dedicated per-task detail page for the polled task (reuses the existing inline-expand row from
  TASK-009).
- File-size limits / upload progress UI.
- Any change to `folder_watch`/TASK-001f, or to `ingest_source`'s/providers' signatures.
- Retroactive context application via any mechanism other than the existing `edit_proposal` endpoint
  (e.g., no new backend endpoint to "set context for a whole ingestion task at once").

## Verification record (2026-09-08)

Verified by Claude in the same session as implementation — same disclosed limitation as every prior
ticket in this project: not a second independent reviewer. Implemented out of strict backlog order at
Cleo's explicit request (TASK-015 remained the officially next ticket) — same precedent as
TASK-016/017/018/019 and TASK-001f/014a/014b before it.

**Blocking dependency status confirmed before starting**: TASK-014a (`completed` 2026-09-08, earlier
in this same day) already made `context` a recognized field — `review/storage.py`'s
`_COMMON_EDITABLE_FIELDS` includes `"context"`, all four `*_path` helpers accept it, `accept_proposal`
reads it per type branch, and `ProposalDetail.jsx` already has a working context editor. This ticket's
context half was therefore immediately meaningful, not just independently testable as the ticket's own
Dependencies section anticipated.

**One correction to the ticket's own text, decided during implementation, not silently picked**: §1's
prose says "400 ValidationError" for a non-`.md`/missing-file upload. `src/app/ingestion/` has no
`errors.py` module and `start_ingestion` (the sibling route in the same file) raises a bare `ValueError`
for its own validation — no AC pins the exact `error.type` string, and `api/errors.py::ValidationError`
exists but is explicitly docstring-scoped to pagination parameters, so reusing it would have been a
semantic misuse of an unrelated exception class. `upload_ingestion` raises plain `ValueError` instead,
consistent with `start_ingestion`'s own convention in the same file.

- `[PASS]` `pytest src/tests/api/` (backend): **124/124 pass**.
- `[PASS]` `pytest src/tests/review/` (backend): **185/185 pass**.
- `[PASS]` `pytest src/tests/ingestion/` (backend): **141/141 pass** (unchanged by this ticket; confirms
  AC9, `ingest_source`'s signature, by the pre-existing regression test already covering it).
- `[PASS]` `pytest --cov` on the three touched backend files
  (`routes_ingestion.py`/`routes_review.py`/`serialization.py`/`review/storage.py`): **100% statement
  coverage** on every one.
- `[PASS]` `npx vitest run` (frontend): **125/125 pass** across 14 files, including the new
  `NewIngestionModal.test.jsx` and the extended `client.test.js`/`IngestionLogs.test.jsx`.
- `[PASS]` `npx vite build`: succeeds, no errors.
- `[PASS]` Manual end-to-end reproduction against a real, isolated scratch vault, a live Flask server,
  and a real local Ollama (`qwen2.5:7b`) — not narrated, actually executed and observed: uploaded a
  real `.md` file via `curl` multipart POST, watched the real ingestion pipeline run to completion (4
  proposals extracted), applied a `context` value to all four via `edit_proposal` (the same call
  `IngestionLogs.jsx`'s polling logic makes), confirmed `GET .../contexts` returned it, confirmed the
  on-disk Proposal frontmatter carried it, and confirmed `accept_proposal` relocated the resulting
  canonical assertion file under a `context`-named top-level folder. Also verified live over HTTP: a
  non-`.md` upload (400), an invalid domain (400), and two same-named uploads producing two distinct
  `_inbox/` files (AC5).
- `[LIMITATION]` No literal browser-driven click-through of `NewIngestionModal`/`IngestionLogs.jsx` —
  this environment has no browser-automation tool available (checked for a project-specific `run`
  skill and `chromium-cli`; neither exists here). The frontend behavior is instead verified via Vitest
  + React Testing Library exercising real component rendering and (for the non-fake-timer tests) real
  simulated user interaction (`@testing-library/user-event`) against a mocked backend, plus the fully
  real backend reproduction above for the half that doesn't depend on browser rendering. Named
  explicitly rather than silently claimed, per this project's own testing discipline.
- `[NOTE]` `@testing-library/user-event`'s realistic-interaction driver hangs indefinitely under
  `vi.useFakeTimers()` even with `delay:null`/`advanceTimers` set (confirmed by isolated repro before
  writing the fix) — the three fake-timer polling tests in `IngestionLogs.test.jsx` (AC13/14/15) use
  the lower-level `fireEvent` instead, which is unaffected. Worth knowing for any future test in this
  suite that combines fake timers with simulated user interaction.

Acceptance criteria checked one by one:

- `[PASS]` AC1 valid `.md` upload → 202, file under `_inbox/<domain>/`, dispatched `ingest_source` call
  matches (backend test + live manual reproduction).
- `[PASS]` AC2 non-`.md` filename → 400, nothing written (backend test + live manual reproduction).
- `[PASS]` AC3 no `file` part → 400 (backend test).
- `[PASS]` AC4 invalid `domain` → 400 before any write (backend test + live manual reproduction).
- `[PASS]` AC5 two same-named uploads → two distinct `_inbox/` files (backend test + live manual
  reproduction).
- `[PASS]` AC6 `GET .../contexts` on an empty domain → `{"contexts": []}` (backend + storage-unit
  tests).
- `[PASS]` AC7 distinct, non-null `context` values across every `proposal_status`/`proposed_item_type`,
  sorted, no duplicates (backend + storage-unit tests).
- `[PASS]` AC8 a malformed Proposal file is skipped by `scan_existing_contexts` without raising
  (storage-unit test, mirrors `scan_proposed_path_segments`'s existing tolerance).
- `[PASS]` AC9 `ingest_source`'s public signature unchanged (pre-existing regression test, untouched by
  this ticket, still passing).
- `[PASS]` AC10 `NewIngestionModal` disables submit with no file; a non-`.md` selection shows an inline
  error and never calls `startIngestionUpload`.
- `[PASS]` AC11 selecting/changing domain fetches/re-fetches `listContexts` for the right domain.
- `[PASS]` AC12 submit with file+domain (no context) calls `startIngestionUpload` once; modal closes,
  list refreshes.
- `[PASS]` AC13 submit with a non-empty context polls `getIngestion` (fake timers) until `completed`,
  then calls `editProposal` once per `proposal_id` with `field_updates.context` set — also confirmed
  live end-to-end against the real backend.
- `[PASS]` AC14 polling stops silently after the 60-attempt cap if no terminal status is reached; no
  error shown.
- `[PASS]` AC15 unmounting mid-poll stops further `getIngestion` calls.
- `[PASS]` AC16 the button/modal exist only on `IngestionLogs.jsx`; full pre-existing frontend suite
  (123 tests before this ticket's additions) still passes unmodified.
