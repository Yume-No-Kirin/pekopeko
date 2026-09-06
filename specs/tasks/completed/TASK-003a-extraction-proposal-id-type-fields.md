# TASK-003a: Extraction Proposal `id`/`type` Fields (V1)

- **Status**: completed

## Objective

Align `extraction/`'s (TASK-003, `completed`) proposal-writing frontmatter with the `id`/`type`
shape `review/` (TASK-002, `completed`) already requires and already produces for assertion
proposals via `ingestion/storage.py::write_proposal_file`. Satellite ticket rather than an
in-place edit to TASK-003's own file, following this project's established convention
(TASK-001a..f, TASK-007a) for extending an already-`completed` ticket without reopening it or
renumbering its acceptance criteria.

Discovered while reading `review/` and `extraction/`'s actual code (not just ticket text) in
preparation for implementing TASK-005: `extraction/storage.py`'s `_base_proposal_frontmatter`
writes `item_type: "proposal"` and no top-level `id` field — `proposal_id` exists only as the
proposal's file/folder name, never in frontmatter. `review/storage.py`'s
`REQUIRED_PROPOSAL_FIELDS` requires top-level `id` and `type`, and `review/pipeline.py` reads
`frontmatter["id"]` directly (`list_proposals`, `get_proposal`). Concretely, **today, every real
extraction-produced entity/event/relationship proposal is silently dropped by
`list_proposals` and returns `400 ValidationError` from `get_proposal`/`accept_proposal`/
`edit_proposal`** — confirmed by reading both modules' actual frontmatter-construction and
validation code side by side, not merely inferred from `docs/ROADMAP.md`'s own note flagging this
gap (dated 2026-09-02, from the project's test-plan "Findings"). Without this fix, TASK-005's new
accept/reject logic for entity/event/relationship has no real proposal it can ever reach.

TASK-003's own "Implementation notes" section documented the `item_type`/no-`id` divergence from
`ingestion/`'s field names as "expected, not an error" — true at the time, since TASK-002
(review, then the only consumer) was assertion-only and never read an extraction-produced
proposal. That reasoning no longer holds once `review/` (TASK-005) becomes a real consumer of
`extraction/`'s proposals: this ticket amends that note for the two specific fields (`id`,
`type`) that are load-bearing for `review/`'s generic (type-agnostic) proposal validation, while
leaving every other named divergence in that note (e.g. Source-file field names) untouched — it
is not a full reconciliation of the two tickets' contracts, only the minimum needed for `review/`
to see these proposals at all.

## Binding context (references, not duplicated here)

- ADI-001 (canonical-persistence-model, Accepted): one file per item, YAML frontmatter + body —
  this ticket adds two frontmatter keys, no new file, no new persistence mechanism.
- ADI-004 (obsidian-role, Accepted): vault layout unchanged by this ticket — `id`/`type` are
  frontmatter fields, not path components.
- `specs/tasks/completed/TASK-003-entity-event-relationship-extraction.md`: "File layout (exact
  contract)" section (defines today's proposal frontmatter fields, amended by this ticket for
  `id`/`type` only) and "Implementation notes" (documents the divergence this ticket narrows).
- `specs/tasks/completed/TASK-002-*.md` / `src/app/ingestion/storage.py::write_proposal_file`
  (lines 224-243): the exact target shape this ticket mirrors — `'id': proposal_id, 'type':
  'proposal'` alongside the fields `extraction/` already writes identically
  (`domain`, `proposal_status`, `proposed_item_type`, `epistemic_status`, `created_at`,
  `valid_from`/`valid_until`, `provenance`).
- `specs/tasks/backlog/TASK-005-entity-event-relationship-review.md`: the ticket this satellite
  unblocks — `review/`'s generic `REQUIRED_PROPOSAL_FIELDS` (`id`, `type`, ...) is what this
  ticket's output must satisfy.

## Scope

1. `extraction/storage.py::_base_proposal_frontmatter` gains a `proposal_id: str` parameter and
   sets two additional frontmatter keys: `"id": proposal_id`, `"type": "proposal"` — literally
   matching `ingestion/storage.py`'s existing assertion-proposal shape for these two fields only.
2. `write_entity_proposal_file`/`write_event_proposal_file`/`write_relationship_proposal_file`
   each generate `proposal_id` *before* calling `_base_proposal_frontmatter` (today generated
   after frontmatter construction, only used for the file path) and pass it through.
3. `REQUIRED_PROPOSAL_FIELDS` (`extraction/storage.py`) gains `"id"` and `"type"`, so a missing
   value on either fails validation the same way every other required field already does.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Only `id`/`type` are added — `item_type` (already `"proposal"`, distinct from
  `proposed_item_type` which holds `entity`/`event`/`relationship`) is left in place unchanged,
  even though it is now redundant with the new `type` field, to avoid touching every existing
  reader/test of `item_type` for no functional gain.
- No change to `write_source_file`/`REQUIRED_SOURCE_FIELDS` — the Source-file field-name
  divergence TASK-003's Implementation notes documented (`item_type`, `source_path`, `content`)
  is untouched; `review/` never reads a Source file's `id`/`type` fields directly (it reads
  `source_id` via a Proposal's `provenance.source_id`, a field already shared).
- No change to `extraction/pipeline.py` — `proposal_id` was already the return value of each
  `write_*_proposal_file` function; this ticket only changes what's written *into* the file the
  same `proposal_id` already names.

## Requirements

- Python only (ADI-007), no new dependency.
- Missing `id`/`type` still fails the same pre-write `_validate_frontmatter` call every other
  required field already goes through — no new validation mechanism.

## Constraints

- No change to `review/`'s code — this ticket's entire fix lives in `extraction/storage.py`.
- No change to the vault file layout/paths.
- No GUI/CLI.

## Files/modules concerned

- `src/app/extraction/storage.py` — `_base_proposal_frontmatter`,
  `write_entity_proposal_file`, `write_event_proposal_file`, `write_relationship_proposal_file`,
  `REQUIRED_PROPOSAL_FIELDS`.
- `src/tests/extraction/` — extend existing proposal-writer tests (or add a new one) asserting
  `id`/`type` are present and correct.

## Dependencies

None as code — narrows a divergence TASK-003 (`completed`) documented as expected. Written and
implemented specifically to unblock TASK-005 (`backlog`), which cannot list/read/accept a real
extraction-produced entity/event/relationship proposal without it.

## Acceptance criteria

1. Writing an entity, event, or relationship proposal produces frontmatter containing `id`
   equal to the same `proposal_id` used for the file's path, and `type: "proposal"`.
2. `REQUIRED_PROPOSAL_FIELDS` includes `id` and `type`; a hand-constructed frontmatter dict
   missing either fails `_validate_frontmatter` with those names listed.
3. A proposal file written by `extraction/`'s writers, when read by `review/storage.py`'s
   `_validate_frontmatter(frontmatter, review.storage.REQUIRED_PROPOSAL_FIELDS)`, no longer fails
   for a missing `id`/`type` (verified directly, without depending on TASK-005's own code, by
   calling `review/`'s existing validation helper against the frontmatter dict this ticket
   produces).
4. No regression: all fields `extraction/storage.py` already wrote before this ticket
   (`item_type`, `domain`, `proposed_item_type`, `epistemic_status`, `provenance`, type-specific
   fields, etc.) are unchanged in name, value, and position in the write order.
5. `grep -r "git"` over `extraction/` still shows no git usage (unaffected by this ticket, kept
   as a regression check).

## Testing requirements

`pytest`, `tmp_path`, no network calls. One test per acceptance criterion above; AC3's test
imports both `extraction.storage` and `review.storage` to exercise `review/`'s real validation
function directly (not a re-implementation of its logic), since that is the one existing check
this ticket exists specifically to satisfy.

## Out of scope

- Reconciling any other field-name divergence between `extraction/` and `review/`/`ingestion/`
  (e.g. Source-file fields) — only `id`/`type` on Proposal files, the two fields load-bearing for
  `review/`'s generic proposal validation.
- Any change inside `src/app/review/` — that is TASK-005's own scope.
- Any GUI or CLI.

## Implementation notes

Implemented 2026-09-05, in the same session as TASK-005 (which this ticket unblocks). Code:
`src/app/extraction/storage.py` — `_base_proposal_frontmatter` gained a `proposal_id` parameter
and now sets `id`/`type` alongside the pre-existing `item_type`; each of
`write_entity_proposal_file`/`write_event_proposal_file`/`write_relationship_proposal_file` now
generates `proposal_id` before building frontmatter (previously generated after, used only for
the file path) and passes it through; `REQUIRED_PROPOSAL_FIELDS` gained `"id"`/`"type"`. New test
file `src/tests/extraction/test_proposal_id_type_fields.py` (7 tests), one of which
(`test_entity_proposal_passes_reviews_own_required_fields_validation`) imports
`src.app.review.storage` directly and runs its real `_validate_frontmatter` against a proposal
this ticket's writers produce — exercising AC3 against the actual consuming code, not a
reimplementation of its logic.

**Wider fallout found and fixed in the same pass**, since this ticket's fix changes real,
previously-broken behavior that several existing tests had encoded as the expected (buggy)
outcome — matching the precedent TASK-007a set ("found two more pre-existing callers with the
same stale assumption... fixed in the same pass as this note"):

- `src/tests/review/conftest.py::make_relationship_proposal_file` defaulted `endpoints` to a
  **dict** (`{"from": "entity-a", "to": "entity-b"}`); the real contract
  (`extraction/providers/base.py`: `endpoints: list[str]`) is a **list**. Fixed to
  `["entity-a", "entity-b"]` — this fixture predates any real endpoint-resolution logic and was
  never exercised against it before TASK-005.
- `src/tests/acceptance/test_ingestion_to_review_end_to_end.py`'s
  `test_entity_event_relationship_extraction_stops_at_proposed_and_accept_is_unsupported` asserted
  that accepting any extraction-produced proposal *fails* with `ValidationError` — the exact bug
  this ticket (plus TASK-005) fixes. Rewritten as
  `test_entity_event_relationship_full_round_trip_creates_traceable_canonical_items`, a real
  success-path test (entities/event accepted, then a relationship whose endpoints resolve to
  their canonical ids).
- `src/tests/api/test_error_mapping.py::test_unsupported_proposal_type_maps_to_422` and
  `src/tests/api/test_review_routes.py::test_accept_entity_proposal_returns_422` both asserted
  TASK-007's original AC10 (422 for any non-assertion accept) — superseded by TASK-005 exactly as
  TASK-012's own ticket text anticipates. First updated to use a genuinely unrecognized
  `proposed_item_type` (`"bogus"`); second renamed and flipped to assert the new `200` success
  path. Left the `409` `UnresolvedRelationshipEndpointError` HTTP mapping itself for TASK-012,
  which explicitly claims that integration point.
- `src/tests/e2e/test_extraction_e2e.py` (marked `pytest.mark.e2e`, excluded by default, **not
  re-run in this session** — no live Ollama available here, flagged `[NOT RUN]` below) existed
  specifically to regression-guard the same bug against a real server. Updated both tests to
  assert the corrected behavior (proposals now visible to the list endpoint; GET/accept on an
  entity proposal now succeed) rather than leaving them to silently start failing the next time
  someone actually runs the e2e suite.

This amends the "expected, not an error" framing in TASK-003's own Implementation notes for the
`id`/`type` fields specifically (see this ticket's Objective) — true when TASK-002/review/ never
read an extraction-produced proposal, no longer true once TASK-005 makes `review/` a real
consumer.

## Verification record

Verified 2026-09-05 by Claude, same session as the implementation (same limitation as every
prior ticket's own verification record: not a second independent reviewer). Environment: working
tree, plus an independent isolated copy (`scratchpad/task005_verify/src`, outside the repo,
`__pycache__` stripped) with `src/tests/extraction/` rerun there separately — identical results.

- `[PASS]` AC1 (entity/event/relationship proposals carry `id` == the file's own `proposal_id`,
  `type: "proposal"`) — `test_entity_proposal_has_id_and_type`,
  `test_event_proposal_has_id_and_type`, `test_relationship_proposal_has_id_and_type`
  (`test_proposal_id_type_fields.py`); also confirmed by eye in `manual_repro.py`'s printed raw
  proposal frontmatter (section 2 of its output).
- `[PASS]` AC2 (`REQUIRED_PROPOSAL_FIELDS` includes `id`/`type`; missing either fails validation
  naming them) — `test_required_proposal_fields_includes_id_and_type`,
  `test_validate_frontmatter_reports_missing_id_and_type`.
- `[PASS]` AC3 (a proposal this ticket's writers produce passes `review/`'s own real
  `REQUIRED_PROPOSAL_FIELDS` validation) —
  `test_entity_proposal_passes_reviews_own_required_fields_validation`, which imports and calls
  `src.app.review.storage._validate_frontmatter` directly (not a reimplementation).
- `[PASS]` AC4 (no regression to pre-existing fields) — `test_pre_existing_fields_unchanged`, plus
  all 4 pre-existing `test_type_specific_fields.py` tests and the rest of `src/tests/extraction/`
  pass unmodified.
- `[PASS]` AC5 (no git usage) — `grep -rni git src/app/extraction/storage.py` returns nothing;
  `test_no_git_usage_in_extraction_module` (pre-existing) still passes.
- `[PASS]` 72/72 `src/tests/extraction/` tests pass (65 pre-existing + 7 new), in the working
  tree and again, independently, in the isolated scratch copy.
- `[PASS]` Coverage — `pytest --cov=src.app.extraction.storage` reports 100% (99/99 statements)
  in both the working tree and the isolated copy; `pytest --cov=src.app.extraction` (whole
  package) reports 100% (423/423 statements) in the isolated copy.
- `[PASS]` Manual end-to-end reproduction (`manual_repro.py`, isolated copy) — real
  `extract_source()` call, raw proposal files read back and printed, confirming `id`/`type`
  present and correct on all 4 written proposals (2 entities, 1 event, 1 relationship).
- `[NOT RUN]` `src/tests/e2e/test_extraction_e2e.py` — no live Ollama/Flask server available in
  this session; updated to assert the corrected behavior (see Implementation notes) but not
  executed. Flagged honestly rather than claimed as verified.
