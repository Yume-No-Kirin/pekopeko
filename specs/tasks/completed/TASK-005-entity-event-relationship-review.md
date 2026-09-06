# TASK-005: Entity, Event and Relationship Proposal Review (V1)

- **Status**: completed

## Objective

Mirror TASK-002's `PROPOSAL -> HUMAN REVIEW -> CANONICAL` workflow for the proposal types
TASK-003 produces (`proposed_item_type` `entity` | `event` | `relationship`), currently
rejected by `review/`'s existing `UnsupportedProposalTypeError` guard. Extends
`src/app/review/` in place: `list_proposals`/`get_proposal` already work generically across
all `proposed_item_type` values; `accept_proposal`/`reject_proposal` must gain type-specific
canonical writers for entity, event, and relationship, plus — for relationship only —
resolution of each endpoint to a stable canonical item id (ADI-003), once/if that endpoint's
own proposal has itself already been accepted.

Independent of `extraction/`'s code: depends only on the Proposal file/frontmatter contract
TASK-003 produces (per ADI-001/ADI-004), not on the `app.extraction` package — matching
`review/`'s existing relationship to `app.ingestion`. Must conform to the Accepted ADRs below
regardless of implementing code.

## Binding context (references, not duplicated here)

- `specs/domain/knowledge-model.md` — same `PROPOSAL -> HUMAN REVIEW -> CANONICAL` slice as
  TASK-002, now for entity/event/relationship.
- ADI-001 (canonical-persistence-model, Accepted): one file per item, YAML frontmatter + body,
  atomic writes. Historization deferred to TASK-006 exactly as TASK-002 already deferred it —
  no `history/` for status-only transitions in this ticket either.
- ADI-003 (relationship-model, Accepted): canonical relationships are structured records naming
  their endpoints by stable item IDs. This ticket performs that resolution for the first time:
  a proposed relationship's `endpoints` (proposal_ids of co-extracted entity/event/relationship
  proposals, or an existing canonical item id, per TASK-003) must be resolved to stable
  canonical ids before the canonical relationship file is written.
- ADI-004 (obsidian-role, Accepted): vault layout `<domain>/<item-type-plural>/<item-id>/<item-id>.md`;
  `entities/`, `events/`, `relationships/` are folders already named by ADI-004 (and referenced
  in TASK-003's binding context) that stay empty until this ticket starts writing to them.
- **Numbering/layout note (added 2026-09-04, while writing TASK-014)**: ADI-012
  (folder-path-organization, Accepted) amends the fixed layout cited above and in "File layout
  (exact contract)" below — but only for `assertion` (TASK-014's own scope). This ticket's file
  layout is **not** rewritten here since entity/event/relationship support for ADI-012's layout
  is explicitly out of TASK-014's scope. Whoever implements this ticket after TASK-014 lands
  must read ADI-012 first and decide there whether `write_entity_file`/`write_event_file`/
  `write_relationship_file` adopt the same `<domain>/<type-plural>/<segments...>/<id>/<id>.md`
  layout (extending this ticket) or intentionally stay on the plain fixed path a while longer —
  a decision for that ticket's own session, not silently assumed by this note.
- ADI-005 (sync-vs-async, Accepted), Rule 3: accept/reject is synchronous — same as TASK-002.
- ADI-007 (implementation-language, Accepted): Python.
- `specs/domain/knowledge-invariants.md`:
  - INV-001: canonical status may only be entered through this reviewed path, applied
    per-item — this rules out auto-cascading acceptance of an unreviewed endpoint (see V1
    scope decisions).
  - INV-003 / INV-012: canonical relationships must carry traceable provenance and lineage to
    the canonical items they connect — motivates blocking acceptance until endpoints are
    themselves canonical, rather than writing a relationship that points at a `proposal_id`.
  - INV-004/INV-018, INV-005, INV-008/INV-009, INV-019 — identical application to TASK-002
    (attributable review via `reviewed_by`/`reviewed_at`, rejection preserves the proposal
    unchanged, domain isolation, a failed canonical write must not leave a proposal
    partially-accepted), just extended to 3 more `proposed_item_type` values.
- `specs/architecture/capabilities.md`: CAP-CORE-002/003/004 (Human Validation, Provenance
  Tracking, Historical State Preservation) — same citations as TASK-002.
- `specs/architecture/technical-requirements.md`: KSR-007/KSR-013, HIR-007/HIR-008 — same
  citations as TASK-002.
- `specs/product/use-cases.md`, UC-011 (Review Queue) — same framing use case; same V1 stage
  scope as TASK-002 (accumulation/listing, individual review, source inspection only).

## Scope

Extend `src/app/review/` so that:

1. `list_proposals` / `get_proposal` continue to work unchanged across all four
   `proposed_item_type` values (already true today; add regression coverage).
2. `accept_proposal` accepts entity and event proposals: writes a canonical file under
   `entities/` or `events/` respectively, carrying over the type-specific fields
   (`entity_type`; `starts_at`/`ends_at`), marks the proposal `ACCEPTED` — same shape as
   TASK-002's assertion path.
3. `accept_proposal` accepts relationship proposals: for each endpoint, resolves it to a
   stable canonical id (see Endpoint resolution below), then writes a canonical file under
   `relationships/` with `endpoints` replaced by their resolved canonical ids, marks the
   proposal `ACCEPTED`.
4. `reject_proposal` rejects entity/event/relationship proposals exactly as it already does
   for assertions: marks `REJECTED`, no canonical write, proposal content unchanged.
5. `UnsupportedProposalTypeError` is narrowed so it only fires for a genuinely unrecognized
   `proposed_item_type` (i.e. something other than assertion/entity/event/relationship).

### Endpoint resolution (relationship acceptance only)

For each identifier in the proposal's `endpoints` list:

- If it matches an existing `proposal_id` in the same domain's `proposals/` folder: that
  proposal's `proposal_status` must already be `ACCEPTED`, and its `resulting_item_id` is used
  as the resolved endpoint. If that proposal is not `ACCEPTED` (still `PROPOSED`, or
  `REJECTED`), `accept_proposal` raises a typed error naming the unresolved endpoint(s) and
  writes nothing — the relationship proposal stays `PROPOSED`. The reviewer must accept the
  endpoint proposal(s) first, then retry.
- If it does not match any `proposal_id`, it is treated as an existing canonical item id (per
  TASK-003's own wording) and used as-is, without being looked up/verified against
  `entities/`/`events/`/`relationships/` on disk (V1 simplification, see V1 scope decisions).
- No auto-cascade: accepting a relationship never accepts another proposal as a side effect
  (INV-001 — each canonicalization is its own explicit, attributable human decision).
- Endpoints may themselves reference other relationship proposals (per TASK-003's "entities,
  events, or other relationships" wording) — the same rule applies uniformly, no special-casing
  by endpoint kind.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Same UC-011 stage scope as TASK-002 (stages 1, 3, 8 only); same exclusions (bulk ops,
  filter/sort beyond status, grouping, dependency inspection, derived-knowledge stats).
- No `EDITED` status, no `history/` subfolder for these transitions — identical to TASK-002,
  deferred to TASK-006.
- No auto-cascade acceptance of endpoint proposals (see above) — a deliberate product decision
  favoring explicit per-item review over reviewer convenience; revisit only as its own future
  ticket if the ordering burden proves too costly in practice.
- An endpoint identifier that resolves to neither an `ACCEPTED` `proposal_id` nor is treated as
  a pre-existing canonical id is **not** verified against the vault's
  `entities/`/`events/`/`relationships/` folders in V1 — it is trusted and written as-is when
  it isn't a recognized `proposal_id`. Validating that a non-proposal endpoint actually exists
  on disk is out of scope (flagged as a possible dangling-reference gap for a future ticket).
- `reviewer_id` and `domain` remain explicit parameters, never inferred — same as TASK-002.
- Downstream impact/staleness analysis (UC-010) remains out of scope.

### File layout (exact contract)

```
<vault_root>/<domain>/entities/<entity_id>/<entity_id>.md
<vault_root>/<domain>/events/<event_id>/<event_id>.md
<vault_root>/<domain>/relationships/<relationship_id>/<relationship_id>.md
<vault_root>/<domain>/proposals/<proposal_id>/<proposal_id>.md   (updated in place, no history/ subfolder)
```

- Fresh ids minted at acceptance: `entity-<uuid4>`, `event-<uuid4>`, `relationship-<uuid4>`
  (mirrors TASK-002's `assert-<uuid4>`).
- `domain` must match the domain already on the target proposal (mismatch -> validation
  error, same as TASK-002).

### Required frontmatter — canonical Entity file (written on acceptance)

`id`, `type: entity`, `domain`, `entity_type` (carried over from proposal), `epistemic_status`
(carried over), `lifecycle_status: ACTIVE`, `valid_from`/`valid_until` (carried over),
`created_at` (acceptance time), `provenance` (`source_id`, `extraction_provider` carried over,
plus `proposal_id`, `reviewed_by`, `reviewed_at`). Body: full copy of the accepted proposal's
body.

### Required frontmatter — canonical Event file (written on acceptance)

Same as Entity, with `starts_at`/`ends_at` (carried over) instead of `entity_type`.

### Required frontmatter — canonical Relationship file (written on acceptance)

Same base fields, plus `relationship_type` (carried over) and `endpoints` (list of resolved
canonical ids, per Endpoint resolution above — never the raw `proposal_id`s).

### Frontmatter added/updated on the Proposal file (accept or reject)

Identical to TASK-002: `proposal_status`, `reviewed_by`, `reviewed_at`, `resulting_item_id`,
`rejection_reason`. All other fields preserved unchanged.

## Requirements

- Same as TASK-002 (Python/pyyaml only, automatic directory creation, pre-write validation, no
  git, atomic writes, canonical write must complete before proposal is marked `ACCEPTED`).
- Endpoint resolution happens before any file is written for a relationship acceptance
  (validate-then-write, same ordering discipline as the rest of the module).

## Constraints

Same list as TASK-002 (no `EDITED` status, no bulk ops, no history/, no database, no GUI/CLI,
no cross-domain review, no auth), plus:
- No auto-cascade acceptance of endpoint proposals.
- No validation of non-proposal endpoint ids against the vault (see V1 scope decisions).
- No dependency on `app.extraction` — only the shared Proposal frontmatter contract.

## Files/modules concerned

- `review/storage.py` — add `write_entity_file` / `write_event_file` / `write_relationship_file`
  (atomic canonical writers), extend frontmatter validation for the 3 new type-specific field
  sets.
- `review/pipeline.py` — extend `accept_proposal` to dispatch by `proposed_item_type`; add
  endpoint resolution logic for relationship acceptance.
- `review/errors.py` — narrow `UnsupportedProposalTypeError`'s trigger condition; add a typed
  error for unresolved (not-yet-accepted) relationship endpoints.
- `tests/review/` — new test files mirroring the above (entity/event acceptance, relationship
  acceptance incl. endpoint resolution success/failure, reject for all 3 types, regression
  coverage for list/get across all 4 types).

## Dependencies

None as code. Depends on TASK-003 only through the shared Proposal frontmatter contract
(ADI-001/ADI-004/TASK-003's file layout) — tests build their own fixture Proposal files rather
than depending on `app.extraction`.

Note: TASK-006 (`backlog`, no code dependency either direction, either order works) also edits
`review/pipeline.py` — it widens `_load_and_validate_for_review`'s status check, while this
ticket adds type-dispatch inside `accept_proposal`. The two changes are orthogonal (status check
vs. type dispatch), but whichever of TASK-005/TASK-006 is implemented second should read the
file's current state (as left by the first) rather than patching against the TASK-002 baseline
described in each ticket's own Objective.

## Acceptance criteria

1. Accepting a `PROPOSED` entity proposal writes `<domain>/entities/<entity_id>/<entity_id>.md`
   with all required frontmatter (`entity_type`, `provenance.proposal_id`, etc.) and updates
   the proposal to `ACCEPTED` with `resulting_item_id` set.
2. Accepting a `PROPOSED` event proposal writes the equivalent canonical Event file with
   `starts_at`/`ends_at` carried over correctly.
3. Accepting a `PROPOSED` relationship proposal whose every endpoint resolves to an `ACCEPTED`
   proposal (or a non-proposal passthrough id) writes the canonical Relationship file with
   `endpoints` replaced by their resolved canonical ids (not the original `proposal_id`s), and
   updates the proposal to `ACCEPTED`.
4. Accepting a relationship proposal with at least one endpoint pointing at a proposal that is
   not yet `ACCEPTED` (still `PROPOSED`, or `REJECTED`) raises a typed error naming the
   unresolved endpoint(s), writes no canonical relationship file, and leaves the relationship
   proposal at `PROPOSED`.
5. Rejecting an entity, event, or relationship proposal sets `proposal_status: REJECTED`,
   `resulting_item_id` stays `null`, no file is written under `entities/`, `events/`, or
   `relationships/`, and the proposal's other fields/body are unchanged.
6. Accept/reject on a non-`PROPOSED` entity/event/relationship proposal raises the same typed
   error as TASK-002's assertion path and leaves all files unchanged.
7. `list_proposals` and `get_proposal` continue to return correct results for a domain
   containing a mix of assertion, entity, event, and relationship proposals (no regression from
   TASK-002).
8. Accepting a relationship never mutates any other proposal file as a side effect (no
   auto-cascade) — verified by asserting an endpoint's still-`PROPOSED` proposal is
   byte-for-byte unchanged after a failed relationship acceptance.
9. All new canonical writes (Entity/Event/Relationship) and proposal in-place updates are
   atomic (temp-file-then-rename), verified the same way as TASK-002's Criterion 8.
10. `grep -r "git"` over `review/` still shows no git usage.

## Testing requirements

`pytest`, `tmp_path`, fixtures built by hand (matching TASK-003's proposal contract), mocked /
no network calls. Minimum cases: entity acceptance (AC1), event acceptance (AC2), relationship
acceptance with all endpoints pre-accepted incl. a non-proposal passthrough endpoint (AC3),
relationship acceptance blocked by an unaccepted endpoint incl. asserting the endpoint
proposal is untouched (AC4, AC8), a relationship-endpoint-references-another-relationship-
proposal case, reject for each of the 3 new types (AC5), double-transition error for each new
type (AC6), mixed-type `list`/`get` regression (AC7), atomicity (AC9), no-git (AC10).

## Out of scope

- `EDITED` status and `history/` for proposals — TASK-006.
- Validating a non-proposal endpoint id actually exists on disk — future ticket if needed.
- Auto-cascade / bulk acceptance of dependency chains — explicit V1 decision above; future
  ticket only if reviewer ordering burden proves costly.
- Adjacency/traversal structure over accepted relationships — TASK-008.
- Any GUI or CLI.
- Cross-domain review, reviewer authentication/authorization — same as TASK-002.

## Implementation notes

Implemented 2026-09-05. A real, previously-undocumented blocker surfaced while reading the actual
`review/`/`extraction/` code (not just this ticket's text, which claims independence from
`extraction/`'s code): `extraction/storage.py`'s proposal writer used a different field contract
(`item_type`, no top-level `id`) than `review/storage.py`'s generic `REQUIRED_PROPOSAL_FIELDS`
(`id`, `type`) requires — so, before this session, `list_proposals` silently dropped every real
extraction-produced entity/event/relationship proposal and `get_proposal`/`accept_proposal`
returned `400` before ever reaching this ticket's own logic. `docs/ROADMAP.md`'s own "État
actuel" already flagged this exact gap ("TASK-005 devra réconcilier les deux contrats de
champs"). Resolved as a new satellite ticket,
`specs/tasks/completed/TASK-003a-extraction-proposal-id-type-fields.md` (mirroring the
TASK-001a..f/TASK-007a precedent), implemented in this same session immediately before this
ticket's own code, since this ticket has no real proposal to operate on without it. See that
ticket's own Implementation notes for the fix and the several existing tests it found asserting
the old (buggy) behavior as expected.

Code, following the ticket's own file list exactly:

- `review/errors.py` — added `UnresolvedRelationshipEndpointError`, pre-named exactly as TASK-012
  (the GUI-integration follow-up, `backlog`) already commits to using — no functional difference
  to name it now vs. when TASK-012 lands, and it saves a rename. Narrowed
  `UnsupportedProposalTypeError`'s docstring (fires only for a `proposed_item_type` outside
  `{assertion, entity, event, relationship}`, not "V1 scope" anymore, per Scope item 5).
- `review/storage.py` — added `REQUIRED_ENTITY_FIELDS`/`REQUIRED_EVENT_FIELDS`/
  `REQUIRED_RELATIONSHIP_FIELDS` (same shape as `REQUIRED_ASSERTION_FIELDS` with the type-specific
  field(s) swapped in); reused the existing `REQUIRED_ASSERTION_PROVENANCE_FIELDS` for all four
  types rather than renaming it (identical field set, renaming buys nothing); added
  `_generate_entity_id`/`_generate_event_id`/`_generate_relationship_id` (`entity-`/`event-`/
  `relationship-` prefixes, exactly as this ticket's own "File layout" section specifies — not
  `assert-`'s pattern by false analogy); added `entity_path`/`event_path`/`relationship_path`
  (plain paths, no `path_segments` — ADI-012's folder-path layout stays assertion-only, per this
  ticket's own "Numbering/layout note"); added `write_entity_file`/`write_event_file`/
  `write_relationship_file` mirroring `write_assertion_file` minus the `path_segments` plumbing.
- `review/pipeline.py` — `_load_and_validate_for_review`'s gate now checks against
  `_SUPPORTED_REVIEW_TYPES = {"assertion", "entity", "event", "relationship"}` instead of
  `!= "assertion"`. `accept_proposal` dispatches by `proposed_item_type`, building each type's
  canonical frontmatter per this ticket's own "Required frontmatter" subsections, then calling the
  matching new writer. New `_resolve_relationship_endpoints` helper: for each endpoint id, a
  `ProposalNotFoundError` on lookup means passthrough as a pre-existing canonical id (this
  ticket's explicit V1 simplification, no disk verification); found but not `ACCEPTED` is
  collected as unresolved; found and `ACCEPTED` resolves to its `resulting_item_id`. Any
  unresolved ids raise `UnresolvedRelationshipEndpointError` naming them, before any file is
  written (validate-then-write). Works uniformly whether an endpoint's own proposal is itself
  entity/event/relationship, satisfying the "endpoints may reference other relationship
  proposals" rule with no special-casing. `reject_proposal` needed no change — already
  type-agnostic.
- `src/tests/review/` — fixed `conftest.py::make_relationship_proposal_file`'s `endpoints`
  default (was a dict, real contract is a list — see TASK-003a's notes); flipped the one
  pre-existing test asserting `UnsupportedProposalTypeError` for `proposed_item_type="entity"`
  into a genuinely-unrecognized-type case (`"bogus"`); added a new
  `test_pipeline_accept_entity_event_relationship.py` (entity/event/relationship acceptance,
  endpoint resolution success/failure incl. a relationship-endpoint-references-another-
  relationship case, no-auto-cascade byte-for-byte check, double-transition errors, write-failure
  atomicity) plus extensions to `test_pipeline_reject.py` (reject for the 3 new types,
  double-transition after reject), `test_pipeline_list_get.py` (mixed-4-type regression), and
  `test_storage.py` (new id generators, path helpers, writers).

**Deliberate naming decision, flagged rather than silently chosen**: `AcceptResult` keeps its
`assertion_id`/`assertion_path` field names for all four `proposed_item_type`s (populated with
whichever type's actual id/path), rather than being generalized to something like
`resulting_item_id`/`resulting_item_path`. `src/app/api/serialization.py::accept_result_to_dict`
hardcodes `result.assertion_path`, and TASK-012's own ticket text scopes its entire API-layer
change to exactly one new error-mapping row in `src/app/api/app.py` — nothing about
`AcceptResult`/serialization. Renaming here would have silently broken the already-`completed`,
already-verified API/frontend accept flow (TASK-007/013/014) for a change outside this ticket's
own file list (`review/` only). This is real naming debt (a field called `assertion_id` can hold
an entity/event/relationship id) — noted here for whoever next touches `AcceptResult`, not fixed
silently.

**Also fixed in this pass**, matching the TASK-007a precedent of fixing tests whose assumptions a
ticket's own change makes stale: `src/tests/acceptance/test_ingestion_to_review_end_to_end.py`'s
UC-001 entity/event/relationship test (previously asserted acceptance *fails*) is now a real
success-path round trip; `src/tests/api/test_error_mapping.py` and `test_review_routes.py`'s two
tests asserting TASK-007's original AC10 (422 for any non-assertion accept — superseded by this
ticket, exactly as TASK-012's own text anticipates) were updated in place; `src/tests/e2e/
test_extraction_e2e.py`'s two tests guarding the same bug against a real server were updated to
assert the corrected behavior (not re-run — no live Ollama in this session, see Verification
record).

## Verification record

Verified 2026-09-05 by Claude, same session as the implementation (same limitation as every prior
ticket's own verification record: not a second independent reviewer). Environment: working tree,
plus an independent isolated copy (`scratchpad/task005_verify/src`, outside the repo,
`__pycache__` stripped) with `src/tests/review/`, `src/tests/extraction/`, `src/tests/api/`, and
`src/tests/acceptance/` rerun there separately — identical results in both.

- `[PASS]` AC1 (entity acceptance writes canonical Entity file with required frontmatter,
  proposal -> `ACCEPTED`/`resulting_item_id`) — `test_accept_entity_proposal_writes_canonical_entity_file`
  (`test_pipeline_accept_entity_event_relationship.py`); also confirmed by eye in
  `manual_repro.py`'s printed canonical entity files.
- `[PASS]` AC2 (event acceptance carries `starts_at`/`ends_at`) —
  `test_accept_event_proposal_writes_canonical_event_file_with_temporal_bounds`.
- `[PASS]` AC3 (relationship acceptance with all endpoints resolvable writes canonical
  Relationship file with resolved ids, not raw `proposal_id`s) —
  `test_accept_relationship_proposal_resolves_accepted_and_passthrough_endpoints`,
  `test_accept_relationship_endpoint_referencing_another_relationship_proposal`; confirmed by eye
  in `manual_repro.py` section 3.
- `[PASS]` AC4 (relationship blocked by an unaccepted endpoint raises a typed error naming it,
  writes nothing, proposal stays `PROPOSED`) —
  `test_accept_relationship_blocked_by_unaccepted_endpoint_raises_and_writes_nothing`,
  `test_accept_relationship_endpoint_rejected_is_also_unresolved`; confirmed by eye in
  `manual_repro.py` section 4 (raised exception printed, `relationships/` dir entries checked).
- `[PASS]` AC5 (reject for entity/event/relationship: `REJECTED`, `resulting_item_id` stays
  `null`, no canonical file, other fields/body unchanged) —
  `test_reject_entity_proposal_sets_status_and_writes_no_canonical_file`,
  `test_reject_event_proposal_sets_status_and_writes_no_canonical_file`,
  `test_reject_relationship_proposal_sets_status_and_writes_no_canonical_file`; confirmed by eye
  in `manual_repro.py` section 5.
- `[PASS]` AC6 (accept/reject on non-`PROPOSED` entity/event/relationship raises the same typed
  error as the assertion path) — `test_double_accept_raises_for_new_types`,
  `test_double_accept_raises_for_relationship`, `test_accept_then_reject_raises_for_entity`
  (`test_pipeline_accept_entity_event_relationship.py`),
  `test_double_transition_after_reject_raises_for_new_types` (`test_pipeline_reject.py`).
- `[PASS]` AC7 (`list_proposals`/`get_proposal` correct for a mix of all 4 types, no regression) —
  `test_list_proposals_returns_all_four_types_mixed`,
  `test_get_proposal_returns_type_specific_fields_for_each_type`
  (`test_pipeline_list_get.py`).
- `[PASS]` AC8 (no auto-cascade: a failed relationship acceptance leaves the endpoint's own
  still-`PROPOSED` proposal byte-for-byte unchanged) — asserted directly inside
  `test_accept_relationship_blocked_by_unaccepted_endpoint_raises_and_writes_nothing`; confirmed
  by eye in `manual_repro.py` section 4 (`original_place_content` comparison).
- `[PASS]` AC9 (all new canonical writes and proposal in-place updates are atomic) — new
  `write_entity_file`/`write_event_file`/`write_relationship_file` reuse the pre-existing,
  already-verified `_write_atomic_file` helper unchanged;
  `test_accept_entity_proposal_write_failure_leaves_proposal_untouched`
  (`test_pipeline_accept_entity_event_relationship.py`) simulates a write failure and confirms no
  partial state, same pattern as TASK-002's own Criterion 8 test for assertions.
- `[PASS]` AC10 (no git usage) — `grep -rni git src/app/review/*.py` returns nothing;
  `test_no_git_references_in_review_module` (pre-existing, unchanged) still passes.
- `[PASS]` 142/142 `src/tests/review/` tests pass (95 pre-existing + 47 new/modified), in the
  working tree and again, independently, in the isolated scratch copy.
- `[PASS]` Coverage — `pytest --cov=src.app.review` reports 100% (379/379 statements) in both the
  working tree and the isolated copy.
- `[PASS]` Regression — `src/tests/extraction/` (72/72, 100% coverage),
  `src/tests/api/` (108/108, 98% overall — pre-existing gaps in `app.py`/`tasks.py`, neither
  touched by this ticket, matching TASK-007a's own documented baseline), and
  `src/tests/acceptance/` (21/21) all rerun independently in both the working tree and the
  isolated copy, identical results. `src/tests/ingestion/` rerun for completeness: 96/98 pass,
  same 2 pre-existing, unrelated failures (`test_acceptance_criteria_compliance`,
  `test_import_isolation`) documented repeatedly for prior tickets — confirmed unrelated, this
  ticket touches no file under `src/app/ingestion/`. `pytest src/tests/` in one shot still fails
  at collection on the pre-existing `test_storage.py`/`_helpers.py` name-collision issue
  documented in `docs/ROADMAP.md`/`specs/tests/test-plan.md` — unrelated to this ticket, not
  fixed (out of scope), worked around by running each package separately as prior tickets already
  do.
- `[PASS]` Manual end-to-end reproduction (`manual_repro.py`, isolated copy) — real
  `extract_source()` + `accept_proposal()`/`reject_proposal()` calls (no mocking of
  extraction/review code), covering: full round trip for 2 entities + 1 event + 1 relationship
  with real endpoint resolution; a second relationship blocked by an unaccepted endpoint,
  confirmed to write nothing and leave the endpoint's proposal untouched; a reject. All resulting
  files inspected by eye, not just asserted by the script.
- `[NOT RUN]` `src/tests/e2e/test_extraction_e2e.py` — no live Ollama/Flask server available in
  this session; both of its tests were updated to assert the corrected behavior (see
  Implementation notes) but not executed. Flagged honestly rather than claimed as verified, same
  posture as every prior ticket's real-Ollama/GUI limitation.
- `[NOT RUN]` GUI interaction — not applicable, no GUI in this ticket's scope (TASK-012 wires the
  frontend, once implemented).
