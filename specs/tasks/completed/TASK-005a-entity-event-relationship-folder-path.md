# TASK-005a: Folder-Path Organization for Entity/Event/Relationship (ADI-012 adoption)

- **Status**: completed

## Objective

Extend ADI-012's folder-path layout — today `assertion`-only — to the three remaining canonical
item types, in both halves it takes to be real:

- **Structure**: `entity_path`/`event_path`/`relationship_path` and their `write_*_file`
  counterparts accept taxonomy segments, `accept_proposal` reads them from the accepted proposal,
  and the reviewer can edit them in the GUI for all four types.
- **Value**: `extraction/`'s `OllamaProvider` proposes those segments at extraction time, the way
  `ingestion/`'s already does for assertions (TASK-001e/ADI-014/ADI-015).

Lettered satellite of TASK-005 (`completed`), whose canonical writers this amends — same
convention as TASK-001a-f / TASK-003a / TASK-007a: don't renumber already-written tickets or
their cross-references.

**This ticket discharges an obligation ADI-012 already carries.** ADI-012's own Scope section
states that `entity`/`event`/`relationship` canonical writers, "once implemented, **must adopt
this same layout** […] but that adoption is that future ticket's own work". The designated future
ticket was TASK-005 itself; when implemented (2026-09-05) it chose to stay on the plain fixed path
— a documented decision, but one that left the requirement without any owning ticket. Found by the
2026-09-07 consistency review; Cleo chose full adoption on 2026-09-07. No new ADR: this applies an
`Accepted` decision, it does not change one.

**Why now rather than later.** TASK-014a establishes "No retroactive relocation" (setting a path
never moves an already-`ACCEPTED` canonical file), which ADI-012/TASK-014 already applied to
assertions. Every entity/event/relationship accepted before this ticket lands therefore stays flat
permanently. The vault holds very few accepted items today (ADI-014 documents verifying against "a
domain with nothing accepted yet"), so the cost of switching is near zero now and only grows.

## Binding context (references, not duplicated here)

- **ADI-012** (`specs/decisions/ADI-012-folder-path-organization.md`, Accepted): the layout being
  adopted — `<domain>/<item-type-plural>/<segments...>/<item_id>/<item_id>.md`, physical
  relocation (not a metadata field), `<domain>` a hard prefix, type folder directly under it,
  empty segments meaning bit-identical backward compatibility. Read it in full first.
- **ADI-014** (Accepted): the mandatory-non-empty guarantee and its retry/fallback machinery,
  scoped by its own text to `ingestion/`'s `OllamaProvider`. This ticket mirrors that posture for
  `extraction/` at a different granularity — see V1 scope decisions.
- **ADI-015** (Accepted): `_normalize_path_string`'s exact rules (HTML-unescape, split on `/`,
  then split each part on `&`/whitespace/`_`/`-` **before** connector-word filtering, strip
  accents incl. `œ`/`æ`, lowercase, drop anything outside `[a-z0-9]`, drop the connector set) and
  the cross-proposal `existing_folders` context. Reimplemented, not imported — see Constraints.
- **TASK-014** (`completed`, `specs/tasks/completed/TASK-014-folder-path-organization.md`): the
  assertion-side implementation this ticket mirrors exactly. Its `_validate_path_segments`,
  `FolderPathBuilder.jsx`, and `GET .../organization-folders` are reused, not re-invented.
- **TASK-001e** (`completed`): the assertion-side LLM path proposal this ticket mirrors for
  `extraction/`, at a different granularity.
- `src/app/review/storage.py`: `_validate_path_segments` (`:100`, reused as-is), `assertion_path`
  (`:131`, the reference implementation to mirror), `entity_path`/`event_path`/
  `relationship_path` (`:141-150`, no `path_segments` parameter at all today),
  `write_assertion_file` (`:268`) vs `write_entity_file`/`write_event_file`/
  `write_relationship_file` (`:283-307`), `_COMMON_EDITABLE_FIELDS`/`EDITABLE_FIELDS_BY_TYPE`
  (`:58-64`), `scan_organization_folders` (`:242`, hardcoded to `assertions/`).
- `src/app/review/pipeline.py::accept_proposal` (`:239-321`): four type-dispatched branches; only
  the assertion branch passes `path_segments` today.
- `src/app/ingestion/providers/ollama_provider.py` (`:20-21`, `:34`, `:217-301`):
  `PATH_PROPOSAL_MAX_ATTEMPTS`, `FALLBACK_PATH_SEGMENTS`, `_normalize_path_string`,
  `_ensure_path_segments`, `_propose_path_with_retry`, `_propose_path`, `_build_path_prompt` — the
  machinery to mirror.
- `src/app/ingestion/storage.py`: `scan_existing_assertion_folders` (`:77`),
  `scan_proposed_path_segments` (`:113`), `_read_frontmatter` (`:101`).
- `src/app/extraction/providers/base.py`: the three `Extracted*` dataclasses, none of which carries
  any path field today. `src/app/extraction/providers/ollama_provider.py`: `extract()` (`:43`),
  `_parse_extraction_result` (`:138`) — note the extraction provider parses **JSON**, unlike
  ingestion's line-based `status: text | path` format.
- `src/app/extraction/storage.py::_base_proposal_frontmatter` (`:136`) and the three
  `write_*_proposal_file` functions (`:160-216`).
- `src/app/api/routes_review.py`: `_VALID_ORGANIZATION_ITEM_TYPES = {"assertion"}` (`:16`) and
  `get_organization_folders` (`:76-85`) — which **already validates** an `item_type` query
  parameter and then ignores it.
- `frontend/src/pages/ProposalDetail.jsx`: the "✎ Éditer" button gated on `assertion` (`:291`),
  the "Dossier proposé" row nested inside the `assertion` block (`:340`, `:391`),
  `handleEditSave` (`:180`), `listOrganizationFolders(domain, "assertion")` (`:171`).
  `frontend/src/pages/Validation.jsx`: `FolderPathBuilder` gated on `assertion` (`:164`),
  `listOrganizationFolders(domain, "assertion")` (`:109`), `folderOptionsByDomain` (`:201`).
- **Invariants cited explicitly** (per AGENTS.md, the 2-3 relevant ones, not a global reference):
  - **INV-001** (Universal Human Validation): a proposed path is a *suggestion* attached to a
    Proposal. It never shortcuts review — the file is written at the chosen path only by
    `accept_proposal`, after a human accepts, exactly as for assertions today.
  - **INV-011** (Representations Are Not Canonical Truth): the folder tree is an organization over
    canonical files, not the knowledge model. Nothing in this ticket may make a path load-bearing
    for reading an item back; id-based lookup stays the only addressing mechanism.
  - **INV-019** (Failures Degrade Safely): a failed or unparseable path proposal must never fail
    the extraction task. It exhausts its retries and falls back, leaving every extracted item
    written and reviewable.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

Confirmed with Cleo on 2026-09-07, while scoping this ticket:

1. **All three types, relationships included.** Full symmetry with ADI-012's literal wording. A
   relationship being a link rather than a browsable object was raised as a reason to exclude it,
   and was rejected — the layout stays uniform across the four canonical types.
2. **The proposed path is guaranteed non-empty**, ADI-014 parity: retry up to
   `PATH_PROPOSAL_MAX_ATTEMPTS` (3), then fall back to `["uncategorized"]` rather than leaving it
   empty or failing the task.
3. **Granularity: once per source note, per type — not per item.** One dedicated Ollama call
   resolves the path for *all* entities of a note, one more for all its events, one more for all
   its relationships. At most three extra calls per note, regardless of item count.

Consequences of decision 3, spelled out rather than left to the implementer:

4. **No inline path attempt, and the extraction prompt is unchanged.** ADI-014's ingestion-side
   design tries a cheap per-assertion `| <path>` suffix first and only calls out for the ones it
   missed. A per-item inline key (the natural JSON equivalent here) would contradict decision 3,
   so it is deliberately not added. `_build_extraction_prompt` and `_parse_extraction_result` are
   untouched — a materially smaller blast radius than TASK-001e had.
5. **This is a real granularity divergence from ADI-014, and it is not a contradiction.** ADI-014
   chose per-assertion explicitly so a note's assertions could land in different thematic folders,
   and bounds itself to `ingestion/`'s provider ("garantie propre à ce provider"). Choosing
   per-note-per-type for `extraction/` follows ADI-016's own precedent, which computes `context`
   once per source note for exactly the reason that applies here: the value does not meaningfully
   vary between items of one type extracted from one note. Recorded as a ticket-level scope
   decision, **not a new ADR** — same posture TASK-016/TASK-018 took for their own scope choices.
6. **`existing_folders` context is per type, never shared across types.** The entity tree and the
   event tree are different taxonomies; feeding one as context for the other would produce
   incoherent suggestions. For the same reason there is **no in-batch accumulation across types**
   (ADI-015 accumulates within one taxonomy, between assertions — which has no analogue here,
   since each type resolves exactly once per call).

## Scope

### A. Structure — `src/app/review/` (mirrors TASK-014 exactly)

1. `entity_path`, `event_path`, `relationship_path` each gain
   `path_segments: list[str] | None = None`, inserted between the type-plural folder and the id
   folder, validated by the **existing** `_validate_path_segments` helper (no new validation
   logic). `None`/omitted produces byte-for-byte today's path — the first thing to test.
2. `write_entity_file`, `write_event_file`, `write_relationship_file` each gain the same optional
   parameter, passed straight through to their `*_path` function. Mirrors `write_assertion_file`.
3. `accept_proposal`'s entity/event/relationship branches each read
   `frontmatter.get("proposed_path_segments")` and pass it as `path_segments=` to their writer —
   one line per branch; the assertion branch already does this. `accept_proposal`'s public
   signature is unchanged.
4. `proposed_path_segments` **moves** out of `EDITABLE_FIELDS_BY_TYPE["assertion"]` and into
   `_COMMON_EDITABLE_FIELDS`, so all four types accept it through `edit_proposal`. TASK-014
   deliberately kept it type-scoped *because* the field was assertion-only; that reason is gone.
   See the trap in §E14 — this one line is what defuses it.
5. `scan_organization_folders(vault_root, domain, item_type="assertion")` gains the parameter: it
   selects the type-plural directory to walk (`assertions`/`entities`/`events`/`relationships`)
   and the id prefix to treat as a leaf and not descend into (`assert-`/`entity-`/`event-`/
   `relationship-`, matching the `_generate_*_id` prefixes). The default preserves every existing
   caller. `_VALID_ORGANIZATION_ITEM_TYPES` widens to all four; `get_organization_folders` passes
   the already-validated `item_type` through instead of discarding it. **No new route, no change
   to the response envelope** — the API surface already anticipated this exact case.

### B. Proposal persistence — `src/app/extraction/`

6. `ExtractedEntity`, `ExtractedEvent`, `ExtractedRelationship`
   (`extraction/providers/base.py`) each gain
   `proposed_path_segments: list[str] = field(default_factory=list)`. Additive; no existing field
   or validation changes.
7. `_base_proposal_frontmatter` (`extraction/storage.py`) writes a `proposed_path_segments` key,
   supplied by each of the three `write_*_proposal_file` functions from the new dataclass field.
   Without this the proposed path never survives to `accept_proposal`, and §A3 has nothing to
   read. `REQUIRED_PROPOSAL_FIELDS` is **not** extended — the key is always written, but a
   hand-written or pre-existing proposal lacking it must still validate and still accept, to the
   flat path.

### C. LLM path proposal — `src/app/extraction/providers/ollama_provider.py`

Independently reimplemented, never imported from `ingestion/` (see Constraints):
`_normalize_path_string` (ADI-015's rules, copied behaviour-for-behaviour),
`PATH_PROPOSAL_MAX_ATTEMPTS = 3`, `FALLBACK_PATH_SEGMENTS = ["uncategorized"]`.

8. New `_ensure_path_segments(result, source_text, context) -> None`, called once from `extract()`
   after `_parse_extraction_result`, mutating in place. For each of the three item lists that is
   **non-empty**: resolve one path via `_propose_path_with_retry`, then assign it to every item in
   that list. A type with no items triggers no call.
9. `_propose_path_with_retry(item_type, items, source_text, existing_folders)` — up to
   `PATH_PROPOSAL_MAX_ATTEMPTS` attempts at `_propose_path`, returning the first non-empty
   normalized result; any exception is caught and counts as a failed attempt (mirrors ingestion's
   own posture); on exhaustion returns `list(FALLBACK_PATH_SEGMENTS)`.
10. `_propose_path` posts to `{base_url}/api/generate` with the provider's configured
    model/temperature/timeout, takes the response's first line, and returns
    `_normalize_path_string(first_line)` — structurally identical to ingestion's.
11. `_build_path_prompt(item_type, items, source_text, existing_folders)` — same shape as
    ingestion's, with two differences following from decision 3: it names the item type
    (entities / events / relationships) and it lists **all** of that type's items from this note
    rather than one item's text, asking for the single folder path that fits them together.
    Reuses ingestion's nomenclature rules and its worked before/after example verbatim (ADI-015:
    one lowercase unaccented French word per segment, never two ideas in one segment,
    broadest-to-most-specific ordering).
12. `existing_folders` per type (decision 6), built from two new scans in `extraction/storage.py`,
    independently reimplemented:
    - `scan_existing_item_folders(vault_root, domain, item_type) -> list[str]` — mirror of
      `scan_existing_assertion_folders`, parameterized by type-plural directory and id prefix.
    - `scan_proposed_path_segments(vault_root, domain, item_type) -> list[str]` — mirror of its
      ingestion namesake, reading `<domain>/proposals/*/*.md`, keeping frontmatter whose
      `proposal_status` is `PROPOSED` or `EDITED` **and** whose `proposed_item_type` matches.
      Needs a small `_read_frontmatter` helper in `extraction/storage.py` (mirror of ingestion's);
      note `yaml` is not currently imported in that module.
    Both degrade to `[]` when `vault_root`/`domain` are absent from the provider `context` dict or
    the directory does not exist — never raise (INV-019), same as ingestion.

### D. Regression this ticket must fix in `src/app/ingestion/`

13. `ingestion/storage.py::scan_proposed_path_segments` does **not** filter on
    `proposed_item_type`: it accepts any proposal in `<domain>/proposals/` carrying
    `proposed_path_segments`. Both pipelines write into that same `proposals/` directory. So the
    moment §B7 lands, assertion path proposals start receiving entity/event/relationship folder
    paths as "existing folders" — cross-taxonomy contamination, a regression **introduced by this
    ticket** if left alone. Add the `proposed_item_type == "assertion"` filter. Minimal amendment
    to TASK-001e's code, flagged here rather than slipped in silently; it is the only file this
    ticket touches under `ingestion/`.

### E. Frontend

14. **Latent trap to defuse first.** `ProposalDetail.jsx::handleEditSave` already sends
    `proposed_path_segments` in `field_updates` **unconditionally, for every type**, while
    `_validate_editable_fields` allows it for `assertion` only. It is unreachable today purely
    because the "✎ Éditer" button is gated on `assertion`. Ungating that button — which this
    ticket does, and which **TASK-014a also needs** for its own `context` editing — produces
    `UneditableFieldError` → `400` on every entity/event/relationship save unless §A4 lands with
    it. Whichever ticket ungates the button must carry §A4 (or TASK-014a's equivalent
    `_COMMON_EDITABLE_FIELDS` change) in the same change.
15. `ProposalDetail.jsx`: ungate the "✎ Éditer" button; move the "Dossier proposé" metadata row
    out of the `proposed_item_type === "assertion"` block so it renders for all four types; fetch
    `folderOptions` with the current proposal's own `item_type` instead of the literal
    `"assertion"`.
16. `Validation.jsx`: remove the `itemType === "assertion"` gate on `FolderPathBuilder`. **This is
    the real work of the frontend half**: the screen renders all four types in one table, so
    `folderOptionsByDomain` must become keyed by domain **and** item type (four
    `listOrganizationFolders` calls per in-scope domain instead of one), with `NoteRow` selecting
    the list matching its own row's type. A domain/type whose fetch fails degrades to `[]`, the
    same posture the file already documents for its existing fetch.

### F. Composition with TASK-014a (`context`, ADI-016)

17. This ticket and TASK-014a (`backlog`) amend **the same** four `*_path` and four `write_*_file`
    functions, both touch `_COMMON_EDITABLE_FIELDS`, and both touch the same two screens. Target
    composed form, whichever lands first:

    ```
    entity_path(vault_root, domain, entity_id, path_segments=None, context=None)
      -> <domain>/entities/<context>/<segments...>/<entity_id>/<entity_id>.md
    ```

    which is exactly the shape ADI-016 already defines for assertions (`context` first, taxonomy
    segments after). The second ticket to land **composes** with the first rather than replacing
    it. Same precedent as the `write_source_file` signature change shared between TASK-016 and
    TASK-017. Neither ticket blocks the other; both are independently implementable and testable.

## Requirements

- **Backend**: Python only (ADI-007), Flask (ADI-010). **No new dependency** — every helper this
  ticket needs already exists in one form or another in the repository.
- **Frontend**: React function components, the existing `api/client.js`/`api/review.js` wrappers,
  the existing `FolderPathBuilder.jsx` reused unchanged. No new frontend dependency, no new
  component, no direct `fetch()` outside `api/client.js`.

## Constraints

- **No import from `ingestion/` into `extraction/`, in either direction.** The path machinery is
  reimplemented, not shared — the module-independence discipline TASK-002 established and that
  `scan_existing_assertion_folders` already follows for its own reimplementation of
  `review/storage.py::scan_organization_folders`. Only the on-disk contract is shared, never code.
  Factoring the two copies together is TASK-037's business, not this ticket's.
- No change to any existing function's **required** parameters: `path_segments` is
  additive-optional throughout, exactly as TASK-014 did for assertions.
- No change to `Provider.extract()`'s interface (`extraction/providers/base.py`), to
  `extract_source`'s public signature, or to `accept_proposal`'s.
- No change to the extraction prompt or to `_parse_extraction_result` (V1 scope decision 4).
- No new HTTP route and no change to any existing route's response shape — `get_organization_folders`
  gains only the pass-through of a parameter it already validates.
- No retroactive relocation: an already-`ACCEPTED` canonical file is never moved, whatever is
  edited afterwards. Same rule ADI-012/TASK-014 set for assertions and TASK-014a restates.
- A failed path proposal never fails the extraction task (INV-019) — it falls back.

## Files/modules concerned

- **Backend, modified in place**: `src/app/review/storage.py` (3 `*_path`, 3 `write_*_file`,
  `_COMMON_EDITABLE_FIELDS`/`EDITABLE_FIELDS_BY_TYPE`, `scan_organization_folders`),
  `src/app/review/pipeline.py` (`accept_proposal`, 3 branches), `src/app/api/routes_review.py`
  (`_VALID_ORGANIZATION_ITEM_TYPES`, `get_organization_folders`),
  `src/app/extraction/providers/base.py` (3 dataclasses),
  `src/app/extraction/providers/ollama_provider.py` (the new path machinery),
  `src/app/extraction/storage.py` (`_base_proposal_frontmatter`, 3 `write_*_proposal_file`, 2 new
  scans, `_read_frontmatter`), `src/app/ingestion/storage.py` (§D13 filter only).
- **Backend, new tests**: `src/tests/review/` (path construction and regression for the 3 types,
  `EDITABLE_FIELDS_BY_TYPE`, scoped `scan_organization_folders`), `src/tests/extraction/`
  (`_normalize_path_string`, `_ensure_path_segments` granularity and fallback, the 2 scans,
  proposal frontmatter), `src/tests/api/` (`organization-folders` for the 4 types),
  `src/tests/ingestion/` (§D13 regression).
- **Frontend, modified in place**: `frontend/src/pages/ProposalDetail.jsx`,
  `frontend/src/pages/Validation.jsx`, plus their existing `.test.jsx` files.
  `FolderPathBuilder.jsx` itself is **not** modified.

## Dependencies

- **TASK-005** (`completed`) — the canonical writers this amends; **TASK-014** (`completed`) — the
  assertion-side implementation this mirrors and whose helpers it reuses; **TASK-012**
  (`completed`) — the GUI already renders all 4 types, which is what makes the frontend half a
  matter of lifting gates rather than building screens; **TASK-013** (`completed`) — the edit-mode
  mechanism §E plugs into; **TASK-001e** (`completed`) + ADI-014/ADI-015 — the machinery mirrored
  in §C and the file amended in §D.
- **ADI-012** (Accepted) — the binding contract; this ticket is its adoption.
- Independent of TASK-015/016/017/018/019 and of TASK-001f. **Soft-coupled to TASK-014a** — see
  §F17 for the composition, and §E14 for the one change neither ticket may ship without.

## Acceptance criteria

Backend — structure:

1. `entity_path(vault_root, domain, entity_id)` with no `path_segments` returns exactly today's
   path; same for `event_path` and `relationship_path`. Byte-for-byte regression test.
2. `entity_path(..., path_segments=["a", "b"])` returns
   `<vault_root>/<domain>/entities/a/b/<entity_id>/<entity_id>.md`; `event_path` and
   `relationship_path` behave symmetrically under their own type folders.
3. A segment containing `/` or equal to `..` is rejected for all three types before any write,
   raising the same `ValidationError` an invalid assertion segment already does — no partial state
   on disk.
4. `accept_proposal` on an entity/event/relationship proposal whose frontmatter carries
   `proposed_path_segments` writes the canonical file under the segmented path for that type; with
   the key absent or `null` it writes to the plain path, for all three types.
5. `edit_proposal` accepts `proposed_path_segments` in `field_updates` for **all four**
   `proposed_item_type` values; a subsequent `GET` reflects the new value and a `history/`
   snapshot exists.
6. `scan_organization_folders(vault_root, domain, item_type="entity")` returns segments from
   `<domain>/entities/` only, never from `assertions/`, and skips `entity-`-prefixed id folders
   as leaves. Called with no `item_type` it behaves exactly as before this ticket.
7. `GET /domains/<domain>/organization-folders?item_type=entity` (resp. `event`, `relationship`)
   returns `200` with the existing `{"segments_by_depth": [...]}` envelope and that type's
   segments; `?item_type=bogus` still returns `400 ValidationError`.

Backend — extraction and value:

8. An `extract()` call producing entities, events and relationships issues **exactly three** path
   proposal calls (one per non-empty type), verified on a mocked HTTP layer — not one per item.
9. Every item of a given type produced by one `extract()` call carries the **same**
   `proposed_path_segments`; the three types carry independently resolved values.
10. A type with zero extracted items triggers **no** path proposal call.
11. When the path call keeps returning unusable output, the items of that type end up with
    `["uncategorized"]` after exactly `PATH_PROPOSAL_MAX_ATTEMPTS` attempts, and the extraction
    task still completes successfully with all its proposals written (INV-019).
12. `_normalize_path_string` applied to a dirty raw string (HTML entities, accents, `œ`, two ideas
    joined by `_`/`-`/`&`, a connector word) yields the same clean single-word lowercase
    `[a-z0-9]` segments as ingestion's implementation does for the same input — asserted against
    the ADI-015 worked example.
13. The proposal file written for an entity/event/relationship carries `proposed_path_segments`
    in its frontmatter; a proposal file lacking the key still validates and still accepts (AC4).
14. `scan_existing_item_folders` and `scan_proposed_path_segments` (extraction) return only the
    requested type's paths, and return `[]` — without raising — for a missing directory or a
    `context` dict lacking `vault_root`/`domain`.
15. **§D13 regression**: `ingestion/storage.py::scan_proposed_path_segments` on a vault containing
    both an assertion proposal and an entity proposal, each with `proposed_path_segments`, returns
    only the assertion's path.

Frontend:

16. `ProposalDetail.jsx` renders the "Dossier proposé" row for all four proposal types, and the
    "✎ Éditer" button is available for all four.
17. Entering edit mode on an entity/event/relationship proposal and saving succeeds (no
    `400`/`UneditableFieldError`) and persists the edited segments — the direct regression guard
    for the §E14 trap.
18. `Validation.jsx` renders an editable `FolderPathBuilder` for all four types, and each row's
    `optionsByDepth` comes from its **own** item type's folder list — a fixture with different
    segment sets per type confirms no row is offered another type's segments.
19. A failed `listOrganizationFolders` call for one domain/type leaves the rest of the screen
    rendering, with that row's options degraded to `[]`.

## Testing requirements

- **Backend**: `pytest`, `tmp_path` for `vault_root`, Flask `app.test_client()` for AC7. Fixtures
  built through `review.storage`'s own writers so they match the real on-disk contract. The three
  path-proposal calls are mocked at the module boundary — **no real Ollama call in the default
  suite**, matching TASK-001e's own testing posture.
- **Frontend**: Vitest + React Testing Library, mocked `client.js`, no real network — fixtures
  covering all four types on both screens, including the per-type `folderOptions` map (AC18).
- One test per acceptance criterion above (19 total). Coverage ≥80% on every file touched
  (AGENTS.md project-wide bar).
- Verification per the project discipline: isolated environment outside the repository, tests
  replayed independently, each acceptance criterion checked one by one, and a written
  line-by-line report in a "Verification record" section of this ticket. Known standing limitation
  to restate rather than hide: verification is done by the same session as the implementation, not
  by an independent second reviewer.

## Out of scope

- Any change to the assertion path behaviour (TASK-014/TASK-001e), beyond the §D13 filter.
- Per-item path granularity for entity/event/relationship (V1 scope decision 3) — if this proves
  too coarse in real use, that is a future amendment, exactly as ADI-014/ADI-015 amended
  TASK-001e after real verification.
- An inline `proposed_path` key in the extraction prompt's JSON (V1 scope decision 4).
- Populating or deriving `context` (ADI-016) — TASK-014a/TASK-014b's scope; this ticket only has
  to compose with them (§F17).
- Relocating already-`ACCEPTED` canonical files.
- Entity dedup/resolution by path or context — no dedup mechanism exists for any type
  (`_generate_entity_id` always mints a fresh UUID); unchanged here, still ADI-016's stated gap.
- Factoring the duplicated path machinery between `ingestion/` and `extraction/` — TASK-037.

## Implementation notes (2026-09-07)

Implemented exactly as scoped, mirroring TASK-014 (§A) and TASK-001e/ADI-014/ADI-015 (§C)
function-for-function, independently reimplemented per the Constraints (no import between
`ingestion/` and `extraction/`).

- **File not in the ticket's own "Files/modules concerned" list, needed anyway**:
  `src/app/extraction/pipeline.py` — one line, the `provider.extract(content, {...})` call site
  (was `{"source_path": str(source_path)}`) gains `"vault_root": vault_root, "domain": domain`,
  mirroring `ingestion/pipeline.py`'s own ADI-014 amendment exactly. Without it, extraction's
  `_ensure_path_segments` has no way to reach `vault_root`/`domain` at all — `Provider.extract(text,
  context)` is the only channel a provider has out to the pipeline (ADI-008's abstraction boundary),
  so §C12's "context dict lacking vault_root/domain" degrade path is only reachable, and the
  existing-folder scan only ever exercised, once this line exists. No signature change —
  `extract_source`'s own parameter list is untouched (regression-tested, see AC verification below).
- **Transcription bug caught by the test suite, not by inspection**: an early draft of
  `_normalize_path_string` copied `part.replace('&amp;', ' ')` from a prior read of ingestion's
  source; the real ingestion file (re-read directly to resolve the discrepancy) has
  `part.replace('&', ' ')` — `html.unescape` already turns `&amp;` into `&` one line earlier, so the
  `&amp;`-literal version was silently dead code that would have left bare `&`-joined segments
  (`"enjeux&themes"`) un-split. Caught immediately by
  `test_normalize_path_string_splits_ampersand_into_separate_segments` failing
  (`['enjeuxthemes']` instead of `['enjeux', 'themes']`); fixed to match the real source exactly, and
  the rest of the copied block (`_propose_path_with_retry`/`_propose_path`/`_build_path_prompt`'s
  exact structure) was re-verified line-by-line against the real file afterward as a precaution.
- **`EDITABLE_FIELDS_BY_TYPE` form** (§A4): `proposed_path_segments` moved into
  `_COMMON_EDITABLE_FIELDS` and the `"assertion"` entry simplified from
  `_COMMON_EDITABLE_FIELDS | {"proposed_path_segments"}` to plain `_COMMON_EDITABLE_FIELDS`, matching
  entity/event/relationship's own `_COMMON_EDITABLE_FIELDS | {type-specific fields}` pattern.
- **`scan_organization_folders`/`scan_existing_item_folders` type-dir maps**: `review/storage.py`'s
  `_ORGANIZATION_ITEM_TYPE_DIRS` covers all four types (it's the one function every existing
  assertion caller already depends on, default-preserved via `item_type: str = "assertion"`);
  `extraction/storage.py`'s `_ITEM_TYPE_DIRS` covers only entity/event/relationship, since
  extraction never proposes an assertion path — a deliberately narrower, independent map, not a
  subset import.
- **`OllamaProviderConfig.temperature`**: extraction's provider had no `temperature` field at all
  (its main JSON-extraction call never set one); added `temperature: float = 0.7` used only by the
  new path-proposal call, matching ingestion's config shape. The main extraction call's payload is
  unchanged (still no `temperature` key), per the ticket's own "extraction prompt is unchanged"
  constraint.
- **§D13 ingestion regression fix test fixtures**: `src/tests/ingestion/test_pipeline.py`'s shared
  `_write_raw_proposal` helper (used only by the six `scan_proposed_path_segments` tests) had no
  `proposed_item_type` in any of its fixtures — harmless before this ticket, but the new filter would
  have excluded all of them once added. Fixed with one default at the helper's single definition site
  (`frontmatter = {"proposed_item_type": "assertion", **frontmatter}`) rather than touching each of
  the nine call sites individually. A separate, unrelated test in
  `src/tests/ingestion/test_ollama_provider.py`
  (`test_extract_merges_accepted_and_pending_proposal_folders_into_context`) built its own raw
  proposal file inline with the same gap; fixed the same way at its one call site.
- Code touched, backend: `src/app/review/storage.py` (`_COMMON_EDITABLE_FIELDS`/
  `EDITABLE_FIELDS_BY_TYPE`, `entity_path`/`event_path`/`relationship_path`, `write_entity_file`/
  `write_event_file`/`write_relationship_file`, `_ORGANIZATION_ITEM_TYPE_DIRS`,
  `scan_organization_folders`), `src/app/review/pipeline.py` (`accept_proposal`, 3 branches),
  `src/app/api/routes_review.py` (`_VALID_ORGANIZATION_ITEM_TYPES`, `get_organization_folders`),
  `src/app/extraction/providers/base.py` (3 dataclasses), `src/app/extraction/providers/ollama_provider.py`
  (`OllamaProviderConfig.temperature`, `_normalize_path_string` + constants, `_ensure_path_segments`,
  `_propose_path_with_retry`, `_propose_path`, `_build_path_prompt`, `extract()`),
  `src/app/extraction/storage.py` (`_base_proposal_frontmatter`, 3 `write_*_proposal_file`,
  `_ITEM_TYPE_DIRS`, `scan_existing_item_folders`, `scan_proposed_path_segments`,
  `_read_frontmatter`), `src/app/extraction/pipeline.py` (context dict, see above),
  `src/app/ingestion/storage.py` (`scan_proposed_path_segments` filter, §D13). Frontend:
  `frontend/src/pages/ProposalDetail.jsx` (Éditer button ungated, Dossier proposé row hoisted out of
  the assertion-only block, `listOrganizationFolders` called with the proposal's own type),
  `frontend/src/pages/Validation.jsx` (`fetchFolderOptionsByDomain` widened to 4 calls/domain keyed
  by type, `NoteRow`'s folder-cell ungated and type-scoped). `FolderPathBuilder.jsx` unmodified, as
  scoped.

## Verification record (2026-09-07)

Verified by Claude in the same session as implementation — same disclosed limitation as every prior
ticket in this project: not a second independent reviewer. Backend tests run per-package (this
repo's `src/tests/` has a pre-existing, documented cross-directory `_helpers.py` collection
collision across packages, unrelated to this ticket — confirmed still present and unrelated by
running the two affected pre-existing failures through `git stash`/`git stash pop` against this
ticket's own changes, see below). All commands run directly against the working tree in place
(`a:\DATA\DEV\pekopeko\pekopeko`), not a separate isolated copy — narrower than TASK-013/014's own
"copy outside the repo" step; flagged here as a real gap against this project's stated verification
discipline, not silently matched to it.

- `[PASS]` `pytest src/tests/review --cov=src/app/review`: **159/159 pass**, 100% coverage on every
  file in the package (`storage.py`/`pipeline.py`/`errors.py`/`frontmatter.py`).
- `[PASS]` `pytest src/tests/api --cov=src/app/api`: **114/114 pass**, `routes_review.py` (the only
  file this ticket touches in `api/`) at 100%; package total 98% (the 2% gap is in `app.py`/`tasks.py`,
  neither touched by this ticket).
- `[PASS]` `pytest src/tests/extraction --cov=src/app/extraction`: **101/101 pass**, 100% coverage on
  every file in the package, including every file this ticket touches.
- `[PASS/KNOWN]` `pytest src/tests/ingestion --cov=src/app/ingestion`: **97/97 pass** plus the same 2
  pre-existing failures TASK-014's own verification record documented
  (`test_comprehensive.py::test_acceptance_criteria_compliance`,
  `test_pipeline.py::test_import_isolation`) — reconfirmed via `git stash` (revert to pre-TASK-005a
  code) / re-run / `git stash pop` that both fail identically without this ticket's changes, i.e. not
  a regression. `storage.py` (the one file this ticket touches in `ingestion/`) at 98%, both missing
  lines pre-existing and outside the §D13 change (line 74 in `_validate_frontmatter`, line 257 in
  `write_proposal_file`'s epistemic-status guard — neither touched here).
- `[PASS]` `npx vitest run --coverage` (frontend): **105/105 pass**. Global coverage 98.46% stmts /
  87.88% branch / 84.28% funcs / 98.46% lines — all four clear the project's configured 80% threshold
  (`vite.config.js`, checked globally over `src/api/**` + `src/pages/**`, not per-file — same
  configuration TASK-014's own record already confirmed).
- `[PASS]` `npx vite build`: succeeds, no errors.
- `[PASS]` Manual end-to-end reproduction, actually executed (not narrated), two levels:
  1. **Pipeline level**: a real `PROPOSED` entity proposal built on disk with
     `proposed_path_segments: ["personnages", "principaux"]`; `pipeline.accept_proposal(...)` called
     for real. Result: written path
     `FICTION/entities/personnages/principaux/entity-<uuid>/entity-<uuid>.md`, `.exists()` = `True`,
     matches `entity_path(..., path_segments=["personnages", "principaux"])` exactly;
     `scan_organization_folders(vault, "FICTION", item_type="entity")` =
     `[["personnages"], ["principaux"]]`; frontmatter (`id`/`type`/`entity_type`) and body correct on
     inspection.
  2. **HTTP level**: a real Flask app (`create_app()`) against the same scratch vault, real requests
     via `app.test_client()`: `GET .../organization-folders?item_type=entity` → `200
     {'segments_by_depth': [['personnages']]}`; `GET .../organization-folders?item_type=bogus` → `400
     {'error': {'type': 'ValidationError', 'message': "item_type must be one of ['assertion',
     'entity', 'event', 'relationship'], ..."}}` (confirms the widened valid-set, not just a generic
     rejection); `GET .../organization-folders?item_type=relationship` against an empty
     `relationships/` tree → `200 {'segments_by_depth': []}` (graceful empty case).
- No real Ollama call — the three path-proposal calls (§C) are mocked at the module boundary
  throughout, matching TASK-001e's own testing posture and this ticket's own Testing requirements
  section. A rendered-browser check of `ProposalDetail.jsx`/`Validation.jsx` was not obtained -
  neither `chromium-cli` nor a local Playwright install was available in this environment, the same
  disclosed limitation every prior frontend ticket in this project has recorded.

Acceptance criteria checked one by one:

- `[PASS]` AC1 (`entity_path`/`event_path`/`relationship_path` no-segments byte-for-byte regression)
  — `test_entity_event_relationship_path_no_segments_matches_current_behavior`.
- `[PASS]` AC2 (with-segments construction, all three types) —
  `test_entity_event_relationship_path_with_segments_inserts_between_type_dir_and_id`.
- `[PASS]` AC3 (`/`/`..` rejected before any write, all three types) —
  `test_entity_event_relationship_path_rejects_invalid_segments`.
- `[PASS]` AC4 (`accept_proposal` writes segmented path when present, all three types) —
  `test_accept_{entity,event,relationship}_proposal_writes_segmented_path_when_proposed_path_segments_present`.
- `[PASS]` AC5 (absent/null → plain path, all three types) —
  `test_accept_writes_plain_path_when_proposed_path_segments_absent` (parametrized ×3),
  `test_accept_entity_proposal_writes_plain_path_when_proposed_path_segments_null`; edit-side —
  `test_edit_proposal_field_update_proposed_path_segments_all_types` (parametrized ×3, replaces the
  old TASK-014-era "uneditable for non-assertion" test).
- `[PASS]` AC6 (`scan_organization_folders(item_type=...)` scoped + excludes own id-prefix +
  default-unchanged) — `test_scan_organization_folders_entity_event_relationship_multi_depth_scan`,
  `test_scan_organization_folders_default_item_type_is_assertion`, plus every pre-existing
  assertion-side test (all still pass unmodified).
- `[PASS]` AC7 (`GET .../organization-folders?item_type=` 200 for entity/event/relationship, 400 for
  a truly-invalid value) — `test_get_organization_folders_{entity,event,relationship}_multi_depth_scan`;
  `test_get_organization_folders_invalid_item_type_returns_400` updated to use `item_type=bogus`
  (was `item_type=entity`, now itself a valid, 200-returning value — the old assertion would have
  been testing the wrong thing had it been left as-is).
- `[PASS]` AC8 (exactly 3 path-proposal calls, one per non-empty type, mocked HTTP) —
  `test_extract_issues_exactly_one_path_proposal_call_per_non_empty_type`.
- `[PASS]` AC9 (same-type items share one path, types resolved independently) —
  `test_extract_same_type_shares_path_independent_types_resolved_independently`.
- `[PASS]` AC10 (zero-item type → no call) — `test_extract_zero_items_of_a_type_triggers_no_path_proposal_call`.
- `[PASS]` AC11 (exhausted retries → fallback after exactly `PATH_PROPOSAL_MAX_ATTEMPTS`, task still
  completes) — `test_path_proposal_falls_back_after_exhausting_retries`,
  `test_path_proposal_swallows_errors_during_retry_then_falls_back`,
  `test_path_proposal_retries_then_succeeds`.
- `[PASS]` AC12 (`_normalize_path_string` matches ingestion's ADI-015 worked example) — 9 tests
  mirroring ingestion's own suite exactly (accents, ligatures, HTML entities, `&`/`vs` splitting,
  underscore/hyphen compounds, stopwords, special characters, the real dirty-string example) — this
  is the suite that caught the `&amp;`-vs-`&` transcription bug (see Implementation notes).
- `[PASS]` AC13 (proposal frontmatter carries `proposed_path_segments`; absent key still
  validates/accepts) — `test_write_{entity,relationship}_proposal_file_includes_proposed_path_segments`,
  `test_write_event_proposal_file_default_proposed_path_segments_is_empty_list`,
  `test_required_proposal_fields_does_not_require_proposed_path_segments`; accept-side absence
  already covered by AC5's tests.
- `[PASS]` AC14 (`scan_existing_item_folders`/`scan_proposed_path_segments` type-scoped, `[]`-safe on
  missing dir/context) — `test_scan_existing_item_folders_*` (3 tests),
  `test_scan_proposed_path_segments_*` (5 tests, including status+type filtering, malformed-file and
  invalid-YAML safety), plus `test_extract_merges_accepted_and_pending_folders_when_vault_root_and_domain_present`
  (integration-level, confirms the union actually reaches the prompt).
- `[PASS]` AC15 (§D13 regression: ingestion's `scan_proposed_path_segments` excludes non-assertion
  proposals) — `test_scan_proposed_path_segments_filters_out_non_assertion_proposals`.
- `[PASS]` AC16 (`ProposalDetail.jsx` renders Dossier proposé + Éditer for all four types) —
  `"TASK-005a AC16"` ×2 in `ProposalDetail.test.jsx` (replaces the old TASK-012 "hides the Éditer
  button" test, which asserted the opposite of this ticket's own goal).
- `[PASS]` AC17 (entity/event/relationship edit+save succeeds, no 400, persists segments — the §E14
  trap regression guard) — `"TASK-005a AC17"` ×2 in `ProposalDetail.test.jsx` (item_type-correct
  `listOrganizationFolders` call; a full edit-mode → add-segment → Sauvegarder round trip with no
  `alert` rendered afterward).
- `[PASS]` AC18 (`Validation.jsx` editable `FolderPathBuilder` for all four types, each row's own
  type's options only) — the updated TASK-012 test (renamed, now asserts every row's `.folder-cell`
  is non-empty) plus a dedicated per-type-differentiated-fixture test confirming no row is offered
  another type's segments.
- `[PASS]` AC19 (a failed fetch for one domain/type degrades to `[]`, rest of the screen renders) —
  dedicated test with a rejected `entity` folders fetch for one domain; the row still renders with a
  working (empty-options) `FolderPathBuilder`, nothing else on the page breaks.

Total: **471 backend tests pass** (159 + 114 + 101 + 97) plus the 2 documented pre-existing,
unrelated ingestion failures; **105 frontend tests pass**. 19/19 acceptance criteria verified.
