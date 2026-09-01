# TASK-006: Proposal EDITED Status and History Versioning (V1)

- **Status**: completed

## Objective

Implement UC-011 stage 5 ("Editing functionality") for `src/app/review/`: let a reviewer edit a
Proposal's content (body and/or a bounded set of frontmatter fields) before making an
accept/reject decision, per the `PROPOSED → EDITED → ACCEPTED → CANONICAL` lifecycle named
explicitly in TCR-002 and KSR-007/KSR-013. This is the first time any Proposal's *content*
changes after creation, so it is also the first ticket that exercises ADI-001's `history/`
snapshot mechanism for Proposals — an obligation TASK-002 explicitly deferred to "the future
`EDITED` ticket" (`specs/tasks/completed/TASK-002-proposal-review-workflow.md`, V1 scope
decisions and Out of scope).

Extends `src/app/review/` in place, same independence posture as TASK-002/TASK-005: depends only
on the Proposal file/frontmatter contract (ADI-001/ADI-004, TASK-001's and TASK-003's own file
layouts), never on `app.ingestion` or `app.extraction` code. Does **not** depend on TASK-005:
`edit_proposal` is generic across all four `proposed_item_type` values (assertion, entity, event,
relationship) because editing only rewrites the Proposal's own frontmatter/body — it never touches
a type-specific canonical writer, so it does not need the canonical Entity/Event/Relationship
writers TASK-005 will add. `accept_proposal`/`reject_proposal` remain assertion-only exactly as
TASK-002 left them; this ticket only widens the *status* they accept (`PROPOSED` or `EDITED`), not
the *type* they accept. A known, deliberate consequence: an entity/event/relationship proposal can
be edited by this ticket but still cannot be accepted until TASK-005 lands (still blocked by the
existing `UnsupportedProposalTypeError`) — flagged here, not treated as a bug to fix in this
ticket.

## Binding context (references, not duplicated here)

- `specs/domain/knowledge-model.md` — Validation: proposed items are "reviewed and
  accepted/rejected/**modified**" before becoming canonical; this ticket implements the modified
  path.
- ADI-001 (canonical-persistence-model, Accepted): "When [a file] changes, the complete previous
  version (full content, not a diff) is copied into a per-item history subfolder — e.g.
  `<item-type>/<item-id>/history/<timestamp>--v<n>.md` — with its own `lifecycle_status: SUPERSEDED`
  and a pointer to whatever superseded it." This ticket applies that rule to Proposals for the
  first time, at `proposals/<proposal_id>/history/`.
- ADI-004 (obsidian-role, Accepted): vault layout `<domain>/<item-type-plural>/<item-id>/<item-id>.md`;
  no new top-level folder — `history/` is a subfolder of an existing `proposals/<proposal_id>/`
  directory, same convention ADI-001 already names.
- ADI-005 (sync-vs-async, Accepted), Rule 3: editing is synchronous, exactly like accept/reject —
  the frontmatter/body write and the history snapshot both apply immediately when the reviewer
  acts; no async task is introduced by this ticket.
- ADI-007 (implementation-language, Accepted): Python.
- `specs/domain/knowledge-invariants.md`:
  - INV-001: an edit alone never canonicalizes anything — `EDITED` still requires a subsequent
    `accept_proposal` call, same review gate as `PROPOSED`.
  - INV-004: "the system must never silently destroy or overwrite historical information" — the
    invariant this ticket exists to satisfy for Proposals; a `history/` snapshot must be written
    and never mutated again once created (see V1 scope decisions on `superseded_by`).
  - INV-005: rejecting an edited proposal still doesn't mean the (edited) content is false —
    identical posture to TASK-002, now also true for `EDITED → REJECTED`.
  - INV-008/INV-009: `domain` stays an explicit parameter; no cross-domain edit.
  - INV-018: edits must be attributable — `edited_by`/`edited_at` on the live proposal, mirroring
    `reviewed_by`/`reviewed_at`.
  - INV-019: a failed write must not silently corrupt state — governs the archive-then-overwrite
    ordering below.
- `specs/architecture/capabilities.md`: CAP-CORE-002/003/004 (Human Validation, Provenance
  Tracking, Historical State Preservation) — CAP-CORE-004 is exercised by this ticket for the
  first time on Proposals.
- `specs/architecture/technical-requirements.md`: KSR-007/KSR-013 (proposal status values
  including `EDITED`, literally); TCR-002 (`PROPOSED → EDITED → ACCEPTED → CANONICAL` /
  `PROPOSED → REJECTED`); HIR-007/HIR-008 (complete proposal/review history) — same citations as
  TASK-002, now actually backed by a `history/` snapshot instead of only
  `reviewed_by`/`reviewed_at`.
- `specs/product/use-cases.md`, UC-011 (Review Queue): Processing Stage 5 "Editing functionality";
  Human Review Points "Editing of proposals"; Canonical Knowledge Changes "Modified proposals
  re-enter review" — confirms editing is its own step, independent of accept/reject, and that an
  edited proposal goes back into the review queue rather than being auto-decided.

## Scope

Extend `src/app/review/` so that:

1. `edit_proposal(vault_root, domain, proposal_id, reviewer_id, body=None, field_updates=None)`
   lets a reviewer change a Proposal's `body` and/or a bounded set of frontmatter fields, for a
   Proposal currently `PROPOSED` or `EDITED`, for **any** `proposed_item_type`.
2. Before overwriting the live Proposal file, the current full file content (frontmatter + body,
   as it stood before this edit) is archived to
   `proposals/<proposal_id>/history/<timestamp>--v<n>.md` with `lifecycle_status: SUPERSEDED` and
   `superseded_by: v<n+1>` added to its frontmatter. The live file is then atomically overwritten
   with the new content, `proposal_status: EDITED`, `edited_by`, `edited_at` set.
3. `accept_proposal`/`reject_proposal` are extended to accept a target whose `proposal_status` is
   `PROPOSED` **or** `EDITED` (currently `PROPOSED` only) — no other change to their existing
   contract (canonical write shape, no-`history/`-on-status-only-transition, assertion-only type
   restriction) from TASK-002.
4. A field in `field_updates` outside the allow-list for that proposal's `proposed_item_type`
   raises a typed error before any file is written.

### Editable fields (allow-list, per `proposed_item_type`)

- Common to all types: `body` (the Proposal's markdown content), `epistemic_status`, `valid_from`,
  `valid_until`.
- `entity`: + `entity_type`.
- `event`: + `starts_at`, `ends_at`.
- `relationship`: + `relationship_type`, `endpoints`.
- `assertion`: no additional fields beyond the common set (TASK-001's Proposal contract has none).

Never editable via `edit_proposal`, regardless of type: `id`, `type`, `domain`,
`proposed_item_type`, `created_at`, `provenance`, `proposal_status`,
`reviewed_by`/`reviewed_at`/`resulting_item_id`/`rejection_reason` (system-managed, untouched by
edit — `proposal_status`/`edited_by`/`edited_at` are set by `edit_proposal` itself, never taken
from `field_updates`).

### History versioning (no new `version` field on the live Proposal)

- At edit time, `n = number of files already present in proposals/<proposal_id>/history/, plus 1`.
  This is the version number of the content *being archived* by this edit (i.e. what was live
  until now).
- Archived snapshot: `proposals/<proposal_id>/history/<timestamp>--v<n>.md`, full copy of the
  pre-edit frontmatter + body, with `lifecycle_status: SUPERSEDED` and `superseded_by: v<n+1>`
  added.
- `superseded_by` is written once and never revisited: for every snapshot except the one
  produced by the most recent edit, `v<n+1>` names another file physically present in `history/`;
  for the snapshot from the most recent edit, `v<n+1>` names the still-live Proposal file (not a
  separate file) — this is a derivable fact (the highest version number not present as a file in
  `history/` is the live file), never stored by mutating an old snapshot. This is deliberate: an
  archived snapshot's own content and frontmatter, once written, must never be touched again
  (INV-004).
- Editing an already-`EDITED` proposal a second (or further) time repeats the same procedure:
  archive current live content as the next `n`, overwrite live file, `proposal_status` stays
  `EDITED`.

### Write ordering (failure safety, mirrors TASK-002's assertion-before-status-update discipline)

Archive the pre-edit content to `history/` **first** (atomic write), then atomically overwrite the
live Proposal file with the new content. If the archive write fails, the live file is left
completely untouched (edit fails, no partial state). If the live-file overwrite fails after a
successful archive, the archived snapshot remains as an inert, harmless extra file, but the live
Proposal's content is unchanged (it is overwritten in place, so a failed `os.replace()` leaves the
pre-edit content intact) — no content is ever lost either way.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- `edit_proposal` is generic across all four `proposed_item_type` values, independent of
  TASK-005 — see Objective for why. Accepting/rejecting an edited entity/event/relationship
  proposal remains blocked until TASK-005 lands; this ticket does not change that restriction.
- No bulk edit; one proposal, one call.
- No restore/rollback to a prior archived version — `history/` is a read-only audit trail in V1,
  same posture TASK-002/TASK-003 took toward other deferred mechanisms.
- No diffing/comparison view between versions — out of scope, a future UI concern (TASK-026) if
  ever needed.
- `reviewer_id` remains an explicit parameter, never inferred — same as TASK-002.
- `domain` remains an explicit parameter (INV-008/AP-005), must match the proposal's own `domain`.
- Calling `edit_proposal` with neither `body` nor `field_updates` (or both empty/`None`) is
  rejected as a no-op edit — must not silently succeed or create an empty history snapshot.

## Requirements

- Python only (ADI-007), `pyyaml` for frontmatter — no new dependency.
- Directory creation for `history/` is automatic.
- `edit_proposal` on a proposal whose `proposal_status` is not `PROPOSED` or `EDITED` raises a
  typed error before any file is touched.
- A `field_updates` key outside the allow-list for the proposal's `proposed_item_type` raises a
  typed error before any file is touched (validate-then-write, same discipline as the rest of the
  module).
- All writes (history snapshot, live Proposal overwrite) are atomic: temp file in the same
  directory, then `os.replace()` or equivalent, matching the existing `_write_atomic_file` pattern
  in `review/storage.py`.
- The history snapshot write must complete before the live Proposal file is overwritten (INV-019 —
  see Write ordering above).
- `accept_proposal`/`reject_proposal`'s only behavioral change is the widened status check
  (`PROPOSED` or `EDITED`); everything else about their contract (from TASK-002) is unchanged.

## Constraints

- No new `version` frontmatter field on the live Proposal file — version numbers are derived from
  `history/` folder contents at edit time (see History versioning above).
- No restore/rollback operation, no diff/comparison view, no bulk edit.
- No change to `accept_proposal`/`reject_proposal`'s type restriction (still assertion-only,
  TASK-005's concern).
- No database — plain files only.
- No GUI or CLI required (Python function entry points suffice).
- No dependency on `app.ingestion`, `app.extraction`, or TASK-005's code.
- No cross-domain edit (INV-009); no authentication/authorization — `reviewer_id` is trusted as
  given, same as TASK-002.

## Files/modules concerned

- `review/pipeline.py` — new `edit_proposal(vault_root, domain, proposal_id, reviewer_id,
  body=None, field_updates=None) -> EditResult`; new `_load_and_validate_for_edit` (status check
  `PROPOSED`/`EDITED`, no `proposed_item_type` restriction — distinct from the existing
  `_load_and_validate_for_review` used by accept/reject); widen `_load_and_validate_for_review`'s
  status check from `!= "PROPOSED"` to `not in {"PROPOSED", "EDITED"}`.
- `review/storage.py` — `EDITABLE_FIELDS_BY_TYPE` allow-list constant; `proposal_history_dir` /
  `proposal_history_path` helpers; `archive_proposal_version` (atomic snapshot write, computes
  `n` from existing `history/` contents, adds `lifecycle_status`/`superseded_by`); frontmatter
  validation for `field_updates` against the allow-list.
- `review/errors.py` — new `UneditableFieldError(ReviewError)`.
- `tests/review/` — new test module (e.g. `test_pipeline_edit.py`) covering edit_proposal; add
  regression cases to existing accept/reject tests for the widened `EDITED` status acceptance.

## Dependencies

None as code. Depends on TASK-002's existing `review/` module (extended in place) and the shared
Proposal frontmatter contract from TASK-001/TASK-003 (ADI-001/ADI-004) — not on TASK-005. Tests
build their own fixture Proposal files (including entity/event/relationship fixtures, to cover
`edit_proposal`'s generic-across-types requirement) rather than depending on `app.extraction`.

Note: TASK-005 (`backlog`, no code dependency either direction, either order works) also edits
`review/pipeline.py` — it adds type-dispatch inside `accept_proposal`, while this ticket widens
`_load_and_validate_for_review`'s status check. The two changes are orthogonal (type dispatch vs.
status check), but whichever of TASK-005/TASK-006 is implemented second should read the file's
current state (as left by the first) rather than patching against the TASK-002 baseline described
in each ticket's own Objective.

## Acceptance criteria

1. Editing a `PROPOSED` assertion proposal's `body` archives the pre-edit full file content to
   `proposals/<proposal_id>/history/<timestamp>--v1.md` (with `lifecycle_status: SUPERSEDED`,
   `superseded_by: v2` added), and updates the live proposal file: new `body`,
   `proposal_status: EDITED`, `edited_by`/`edited_at` set, all other fields unchanged.
2. Editing an allow-listed frontmatter field instead of/alongside `body` works correctly for each
   `proposed_item_type` — at minimum: `epistemic_status` (assertion), `entity_type` (entity),
   `starts_at`/`ends_at` (event), `relationship_type` and `endpoints` (relationship) — only the
   passed field(s) change, everything else is carried over unchanged.
3. Passing a `field_updates` key outside the allow-list for that proposal's `proposed_item_type`
   (e.g. `id`, `domain`, `provenance`, or `endpoints` on an assertion proposal) raises
   `UneditableFieldError` before any file is written; live file and `history/` remain untouched.
4. Editing an already-`EDITED` proposal a second time creates a second, independent snapshot
   (`--v2.md`) alongside the first (`--v1.md`); the first snapshot's content and `superseded_by`
   are confirmed byte-for-byte unchanged after the second edit.
5. `edit_proposal` succeeds for a `PROPOSED` proposal of each of the four `proposed_item_type`
   values (assertion, entity, event, relationship) — including entity/event/relationship, even
   though `accept_proposal` cannot yet act on them (still `UnsupportedProposalTypeError`, per
   TASK-005's future scope).
6. Calling `edit_proposal` with neither `body` nor `field_updates` (or both empty) raises
   `ValidationError`; no files touched.
7. Calling `edit_proposal` on a proposal whose `proposal_status` is `ACCEPTED` or `REJECTED`
   raises `InvalidProposalStatusError`; no files touched.
8. `accept_proposal` succeeds on an `EDITED` assertion proposal (in addition to `PROPOSED`),
   writing the canonical Assertion from the current (edited) body/fields — same output contract
   as TASK-002's Criterion 1 otherwise.
9. `reject_proposal` succeeds on an `EDITED` proposal (in addition to `PROPOSED`), setting
   `REJECTED`, `resulting_item_id` stays `null`, and the edited content is preserved unchanged —
   same output contract as TASK-002's Criterion 2 otherwise.
10. Accept/reject on a proposal whose status is neither `PROPOSED` nor `EDITED` (e.g. already
    `ACCEPTED`/`REJECTED`) still raises `InvalidProposalStatusError` and leaves all files
    unchanged — regression coverage for TASK-002's existing Criterion 4.
11. If the `history/` archive write fails (simulated), the live Proposal file is left completely
    unchanged (still its pre-edit content/status) and no partial/orphaned history file remains.
12. All history-snapshot writes and live-file edit overwrites are atomic (temp-file-then-rename),
    verified the same way as TASK-002's Criterion 8.
13. `grep -r "git"` over `review/` still shows no git usage.

## Testing requirements

`pytest`, `tmp_path`, hand-built fixture Proposal files (matching TASK-001's and TASK-003's
contracts) for each `proposed_item_type`, no network calls. Minimum cases: body edit (AC1), each
type's allow-listed field edit (AC2), uneditable-field rejection (AC3), double-edit snapshot
independence (AC4), edit works across all 4 types (AC5), no-op edit rejection (AC6), edit blocked
on `ACCEPTED`/`REJECTED` (AC7), accept from `EDITED` (AC8), reject from `EDITED` (AC9), accept/
reject still blocked outside `{PROPOSED, EDITED}` (AC10), simulated archive-write failure (AC11),
atomicity (AC12), no-git (AC13).

## Out of scope

- Restore/rollback to a prior `history/` version — future ticket if ever needed.
- Diff/comparison view between versions — future UI concern (TASK-026), not this ticket.
- Bulk edit.
- Widening `accept_proposal`/`reject_proposal`'s type restriction beyond assertion — TASK-005.
- Any GUI or CLI.
- Cross-domain edit, reviewer authentication/authorization — same as TASK-002.

## Verification record (2026-09-01)

Implemented by Claude (this session) as an in-place extension of `src/app/review/` (`errors.py`,
`storage.py`, `pipeline.py`), plus new/extended tests in `src/tests/review/` (`conftest.py`,
`test_pipeline_edit.py` new, `test_storage.py`/`test_pipeline_accept.py`/`test_pipeline_reject.py`
extended). Per this project's verification discipline: code was copied to an isolated scratch
directory outside the repo (`/tmp/task006_verify/`) and the full `src/tests/review/` suite re-run
independently there (94/94 pass, 100% line coverage), rather than trusting the in-repo run alone.
Each acceptance criterion checked individually:

- `[PASS]` AC1 (body edit archives pre-edit content to `history/<ts>--v1.md` with
  `lifecycle_status: SUPERSEDED`/`superseded_by: v2`, live file updated with new body,
  `proposal_status: EDITED`, `edited_by`/`edited_at` set, other fields unchanged) —
  `test_edit_proposal_body_archives_pre_edit_content_and_updates_live_file` passes in both runs.
  Also manually reproduced end-to-end outside pytest (hand-built fixture, called `edit_proposal`
  directly, inspected the live file and the archived `v1` snapshot by eye — output matches contract
  exactly, including `superseded_by: v2` on the archived copy).
- `[PASS]` AC2 (allow-listed field edit works per type, only passed field(s) change) —
  `test_edit_proposal_field_update_assertion`/`_entity`/`_event`/`_relationship` pass, one per
  `proposed_item_type`, using new `make_entity_proposal_file`/`make_event_proposal_file`/
  `make_relationship_proposal_file` fixtures added to `conftest.py`.
- `[PASS]` AC3 (disallowed `field_updates` key raises `UneditableFieldError` before any write) —
  `test_edit_proposal_uneditable_field_raises_before_any_write` (`id`),
  `test_edit_proposal_uneditable_cross_type_field_raises` (`endpoints` on an assertion),
  `test_edit_proposal_system_managed_field_raises` (`provenance`) all pass; each asserts the live
  file is byte-identical to before and no `history/` dir was created.
- `[PASS]` AC4 (editing an already-`EDITED` proposal again creates an independent `v2` snapshot,
  `v1` unchanged) — `test_edit_proposal_twice_creates_independent_snapshots` passes, explicitly
  comparing `v1`'s file bytes before/after the second edit. Also manually reproduced: double-edit
  script confirms `v1` byte-for-byte identical after the second edit, `v2` carries
  `superseded_by: v3`.
- `[PASS]` AC5 (`edit_proposal` succeeds for all 4 `proposed_item_type` values) —
  `test_edit_proposal_succeeds_for_assertion`/`_entity`/`_event`/`_relationship` all pass.
- `[PASS]` AC6 (no `body` and no/empty `field_updates` raises `ValidationError`, no-op) —
  `test_edit_proposal_no_body_and_no_field_updates_raises_validation_error` and
  `test_edit_proposal_empty_field_updates_and_no_body_raises_validation_error` pass, both confirming
  the live file is untouched and no `history/` dir is created.
- `[PASS]` AC7 (edit on `ACCEPTED`/`REJECTED` proposal raises `InvalidProposalStatusError`, no
  files touched) — `test_edit_proposal_on_accepted_proposal_raises_invalid_status` and
  `test_edit_proposal_on_rejected_proposal_raises_invalid_status` pass.
- `[PASS]` AC8 (`accept_proposal` succeeds on `EDITED`, writes canonical Assertion from the
  edited body/fields) — `test_accept_proposal_succeeds_on_edited_status` (status-check regression)
  and `test_accept_proposal_after_edit_writes_assertion_from_edited_body_and_fields` (integration:
  calls `edit_proposal` then `accept_proposal`, confirms the resulting Assertion body/fields reflect
  the edit, not the original) both pass.
- `[PASS]` AC9 (`reject_proposal` succeeds on `EDITED`, edited content preserved unchanged) —
  `test_reject_proposal_succeeds_on_edited_status` and
  `test_reject_proposal_after_edit_preserves_edited_content_unchanged` (integration: edit then
  reject, confirms the live file still holds the edited body, not the original) both pass.
- `[PASS]` AC10 (accept/reject still blocked outside `{PROPOSED, EDITED}`) — TASK-002's original
  regression tests (`test_reject_already_rejected_proposal_raises_invalid_status`,
  `test_reject_then_accept_raises_invalid_status`, `test_reject_accepted_proposal_raises_invalid_status`,
  `test_accept_already_accepted_proposal_raises_and_leaves_files_unchanged`,
  `test_accept_then_reject_raises_invalid_status`) all pass unmodified; plus two new
  edit-path-specific cases (`test_accept_already_edited_then_accepted_proposal_raises_on_second_accept`,
  `test_reject_already_edited_then_rejected_proposal_raises_on_second_reject`) confirming the
  widened check still correctly excludes `ACCEPTED`/`REJECTED`.
- `[PASS]` AC11 (simulated archive-write failure leaves the live file untouched, no orphaned
  history file) — `test_edit_proposal_archive_write_failure_leaves_live_file_untouched` and
  `test_edit_proposal_archive_write_failure_no_orphaned_history_file` pass, via monkeypatching
  `storage.archive_proposal_version` to raise before any file is touched.
- `[PASS]` AC12 (all history-snapshot writes and live-file edit overwrites are atomic) —
  `test_edit_proposal_archive_write_is_atomic_no_partial_file_on_replace_failure` (monkeypatches
  `os.replace` to fail on the first call, confirms no partial/orphaned file) and
  `test_edit_proposal_live_overwrite_failure_leaves_archived_snapshot_and_pre_edit_live_content`
  (monkeypatches `os.replace` to fail specifically on the *second* call, confirming the archived
  snapshot survives as an inert extra file while the live proposal file's pre-edit content is left
  intact) both pass — same idiom as `test_storage.py`'s existing `_write_atomic_file` atomicity
  test, applied to the two-write `edit_proposal` sequence specifically.
- `[PASS]` AC13 (no git usage) — `grep -rin "git" src/app/review/` returns nothing (checked
  independently, not just via `test_no_git.py`, which also passes and automatically covers the new
  files since it globs `*.py`).
- `[PASS]` Test coverage — `pytest --cov=src.app.review` reports 100% line coverage (258/258
  statements), in both the working tree and the isolated copy (project requirement: ≥80%). Two
  branches not exercised by any of the 13 ACs directly (`DomainMismatchError` and empty-`reviewer_id`
  in the new `_load_and_validate_for_edit`) were given explicit regression tests
  (`test_edit_proposal_wrong_domain_raises_domain_mismatch`,
  `test_edit_proposal_missing_reviewer_id_raises_validation_error`) to close the gap, matching the
  module's existing near-100% standard.
- `[PASS]` 94/94 tests pass in the working tree and again, independently, in an isolated scratch
  copy of the code (not just re-running in place).
- `[NOT RUN]` Real Obsidian vault / GUI interaction — not applicable, ticket has no GUI/CLI
  requirement (function entry points only, per Constraints).

**Honesty note on independence**: this verification was performed by the same Claude session that
wrote the implementation, not by a separate reviewer or model — same limitation flagged in
TASK-001a/TASK-001b/TASK-002/TASK-003/TASK-004's own verification records. It does follow the
isolated-copy-and-independently-rerun discipline the project asks for, and includes a byte-level
manual end-to-end reproduction (not just trusting pytest's assertions), but is not the same
strength of evidence as an independent second reviewer.
