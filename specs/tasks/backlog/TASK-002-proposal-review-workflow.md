# TASK-002: Proposal Review Workflow (V1)

- **Status**: backlog

## Objective

Implement the second half of the canonical flow in `specs/domain/knowledge-model.md`: `PROPOSAL → HUMAN REVIEW → CANONICAL KNOWLEDGE`. Given Proposal items produced by TASK-001's ingestion pipeline (`proposal_status: PROPOSED`), provide: listing pending proposals, retrieving a single proposal with its source for review, and recording an accept/reject decision. Accepting writes a new canonical `Assertion` file and marks the proposal `ACCEPTED`. Rejecting marks the proposal `REJECTED` and writes no canonical output. Downstream consequence/staleness analysis (UC-010) is out of scope — nothing canonical exists yet to have dependents.

Independent of TASK-001's code: depends only on the Proposal/Source file+frontmatter contract TASK-001 produces (per ADI-001/ADI-004), not on its `ingestion/` package. Must conform to the Accepted ADRs below regardless of implementing code.

## Binding context (references, not duplicated here)

- `specs/domain/knowledge-model.md` — defines Validation (proposed items reviewed and accepted/rejected/modified before becoming canonical) and Canonical Knowledge (human-reviewed, authoritative basis for reasoning).
- ADI-001 (canonical-persistence-model, Accepted): one file per item, YAML frontmatter + body, atomic writes. Historization rule (AP-004): on content change, copy previous version into per-item `history/` with `lifecycle_status: SUPERSEDED` before writing — **this ticket deliberately does not apply that rule to accept/reject transitions**; see V1 scope decisions.
- ADI-004 (obsidian-role, Accepted): vault layout `<domain>/<item-type-plural>/<item-id>/<item-id>.md`; `assertions/` folder already named — no new folder convention introduced.
- ADI-005 (sync-vs-async, Accepted), Rule 3: accept/reject is synchronous; the canonical write applies immediately. Any downstream consequence analysis it triggers is separate async future work — not implemented here.
- ADI-007 (implementation-language, Accepted): Python.
- `specs/domain/knowledge-invariants.md`:
  - INV-001: canonical status may only be entered through this reviewed acceptance path.
  - INV-004/INV-018: a review decision must be attributable — satisfied here by `reviewed_by`/`reviewed_at` on the proposal (not a `history/` snapshot; see V1 scope decisions).
  - INV-005: rejecting must never delete the proposal, alter its content, or mark it false — the file stays on disk with `proposal_status: REJECTED`.
  - INV-008/INV-009: `domain` is explicit; no cross-domain review.
  - INV-019: a failed canonical write must not leave the proposal marked `ACCEPTED` or leave an orphaned assertion file.
- `specs/product/capabilities.md`, CAP-002: all canonical knowledge is human-reviewed; AI-generated content cannot auto-become canonical.
- `specs/architecture/capabilities.md`: CAP-CORE-002/003/004 (Human Validation, Provenance Tracking, Historical State Preservation).
- `specs/architecture/technical-requirements.md`: KSR-007/KSR-013 (proposal status values `PROPOSED, EDITED, ACCEPTED, REJECTED, SUPERSEDED`; review history with timestamp/reviewer); HIR-007/HIR-008 (complete proposal/review history) — satisfied in V1 by `reviewed_by`/`reviewed_at`/`resulting_item_id` on the proposal file (full snapshot historization deferred to the future `EDITED` ticket).
- `specs/product/use-cases.md`, UC-011 (Review Queue) is the framing use case; see V1 scope decisions for which of its stages are covered.

## Scope

Python package providing:

1. List proposals in a domain, optionally filtered by `proposal_status`.
2. Retrieve one proposal's full detail plus its linked Source file content (resolved via `provenance.source_id`).
3. Accept a proposal: write a new canonical `Assertion` item, mark the proposal `ACCEPTED`.
4. Reject a proposal: mark `REJECTED`, optional reason. Never writes a canonical item.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- Only individual review is in scope: UC-011 stages 1 (accumulation/listing), 3 (individual review), 8 (source/context inspection). Out: stage 2 (categorization), 4 (bulk ops), 6 (filter/sort), 7 (grouping/prioritization), 9 (dependency inspection — nothing canonical exists yet), and "Derived Knowledge" (stats/analytics).
- Only `proposed_item_type: assertion` proposals are handled (the only type TASK-001 produces). Entity/Event/Relationship proposals are future work.
- No `EDITED` status — only `PROPOSED → ACCEPTED` and `PROPOSED → REJECTED`. Editing proposal content is a separate future ticket.
- No `history/` snapshot subfolder for accept/reject. ADI-001's snapshot rule is deferred to the future `EDITED` ticket (where content actually changes). An accept/reject transition changes only status metadata, so the proposal file is updated in place (atomically), recording `reviewed_by`/`reviewed_at`/`resulting_item_id` — satisfying INV-004/INV-018/HIR-007/HIR-008 without a snapshot. **Deliberate scope boundary**: the future `EDITED` ticket must introduce `history/` for Proposals.
- `reviewer_id` is an explicit parameter, never inferred (no auth mechanism; single-user product model).
- `domain` is an explicit parameter (INV-008/AP-005).
- Downstream impact/staleness analysis (UC-010) is out of scope.

### File layout (exact contract)

```
<vault_root>/<domain>/assertions/<assertion_id>/<assertion_id>.md
<vault_root>/<domain>/proposals/<proposal_id>/<proposal_id>.md   (updated in place, no history/ subfolder)
```

- `domain` ∈ {PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING}, passed explicitly, must match the `domain` already on the target proposal (mismatch → validation error).
- `assertion_id`: fresh unique ID minted at acceptance, e.g. `assert-<uuid4>`.
- No writes to `sources/`; the linked Source file (via `provenance.source_id`) is read-only.
- Each `.md` file: YAML frontmatter (`---`-delimited) + markdown body.

### Required frontmatter — canonical Assertion file (written on acceptance)

- `id` — matches `assertion_id`
- `type` — `assertion`
- `domain` — same as the source proposal
- `epistemic_status` — carried over unchanged from the proposal
- `lifecycle_status` — `ACTIVE`
- `valid_from` / `valid_until` — carried over unchanged from the proposal
- `created_at` — ISO 8601, acceptance time (not the proposal's own `created_at`, which stays the extraction time, per INV-007)
- `provenance` (dict) — at minimum `source_id`, `extraction_provider` (both carried over from the proposal), plus `proposal_id`, `reviewed_by`, `reviewed_at`

Body: full copy of the accepted proposal's body (extracted assertion text) — a snapshot, not a reference, per ADI-001.

### Frontmatter added/updated on the Proposal file (accept or reject)

- `proposal_status` — `ACCEPTED` or `REJECTED` (overwrites `PROPOSED`)
- `reviewed_by` — the `reviewer_id` passed by the caller
- `reviewed_at` — ISO 8601 timestamp
- `resulting_item_id` — new `assertion_id` if accepted, else `null`
- `rejection_reason` — optional free-text on rejection, else `null`

All other fields written by TASK-001 (`id`, `type`, `domain`, `proposed_item_type`, `epistemic_status`, `created_at`, `valid_from`/`valid_until`, `provenance`) are preserved unchanged.

## Requirements

- Python only (ADI-007). `pyyaml` for frontmatter — no other new dependency without stated reason.
- All directory creation (`assertions/` domain folder, per-item folder) automatic.
- Accept/reject on a proposal whose `proposal_status` is not `PROPOSED` raises a typed error before any file is touched.
- Missing/invalid required frontmatter (read from the proposal, or to be written to the new assertion) raises a typed validation error before any file is written.
- No git anywhere (ADI-001). No dependency on Obsidian being installed/running.
- All writes (new Assertion files, in-place Proposal updates) are atomic: temp file in the same directory, then `os.replace()` or equivalent.
- The Assertion write must complete before the Proposal is updated to `ACCEPTED` (INV-019: a failed assertion write leaves the proposal at `PROPOSED`, never partially accepted).

## Constraints

- No `EDITED` status, no proposal content editing.
- No bulk accept/reject; no filter/sort/group beyond a single optional `status` filter on listing.
- No review statistics, analytics, or dependency/impact inspection.
- No `history/` subfolder for proposals in this ticket.
- No database — plain files only.
- No GUI or CLI required (Python function entry points suffice).
- No dependency on `ingestion/` (TASK-001), `knowledge_core/`, or any other existing module — only the shared file/frontmatter contract. Tests build their own fixture Proposal/Source files.
- No cross-domain review (INV-009).
- No authentication/authorization — `reviewer_id` is trusted as given.

## Files/modules concerned

Suggested layout (adjust if a clearer structure emerges, keep module boundaries matching responsibilities):

- `review/storage.py` — atomic write for the new Assertion file; atomic in-place update for the Proposal file; frontmatter validation for both.
- `review/pipeline.py` — orchestration: `list_proposals(vault_root, domain, status=None) -> list[ProposalSummary]`, `get_proposal(vault_root, domain, proposal_id) -> ProposalDetail` (includes resolved Source content), `accept_proposal(vault_root, domain, proposal_id, reviewer_id) -> AcceptResult`, `reject_proposal(vault_root, domain, proposal_id, reviewer_id, reason=None) -> RejectResult`.
- `tests/review/` — mirrors the modules above.

## Dependencies

None as code. Depends on TASK-001 only through the shared Proposal/Source frontmatter contract (ADI-001/ADI-004) — implementable and testable against hand-built fixtures even before TASK-001 exists.

## Acceptance criteria

1. Accepting a `PROPOSED` proposal produces `<domain>/assertions/<assertion_id>/<assertion_id>.md` with all required frontmatter (including `provenance.proposal_id`, and `provenance.source_id`/`extraction_provider` carried over correctly), and updates the Proposal's `proposal_status` to `ACCEPTED` with `reviewed_by`, `reviewed_at`, `resulting_item_id` = new `assertion_id`.
2. Rejecting a `PROPOSED` proposal sets `proposal_status: REJECTED`, `reviewed_by`/`reviewed_at` set, `resulting_item_id` stays `null`; no file written under `<domain>/assertions/`; the proposal's other fields (incl. body) unchanged.
3. After either transition, the proposal file is updated in place — no `history/` subfolder under `proposals/<proposal_id>/`.
4. Accept/reject on a non-`PROPOSED` proposal raises a typed error and leaves the target proposal file and `<domain>/assertions/` unchanged.
5. If the Assertion write fails (simulated), the proposal stays `PROPOSED`, no orphaned/partial Assertion file remains, and the proposal file is otherwise untouched.
6. `list_proposals(vault_root, domain, status="PROPOSED")` returns exactly that domain's `PROPOSED` proposals — excludes other domains and other statuses.
7. `get_proposal(vault_root, domain, proposal_id)` returns the proposal's frontmatter/body plus the resolved content of its linked Source file (`provenance.source_id`).
8. All Assertion writes and Proposal in-place updates are atomic — verified by code inspection (temp-file-then-rename) or by simulating a mid-write failure and confirming no partial file remains.
9. `grep -r "git"` over `review/` shows no git tooling/libraries used for historization.

## Testing requirements

`pytest` unit tests covering every acceptance criterion, using `tmp_path` (or equivalent) as `vault_root` — never touch a real vault or write outside the test's temp directory. Tests build their own fixture Proposal/Source files (matching TASK-001's contract) rather than depending on TASK-001's code. Include at least:
- Accept flow: full Assertion file/frontmatter contract + updated Proposal fields (Criterion 1).
- Reject flow: updated Proposal fields + absence of any assertion file (Criterion 2).
- No `history/` subfolder created by either transition (Criterion 3).
- Double-transition (accept→accept, accept→reject, reject→accept): typed error, no side effects (Criterion 4).
- Simulated assertion-write failure (Criterion 5).
- Domain isolation for `list_proposals` (Criterion 6).
- `get_proposal` includes resolved Source content (Criterion 7).

## Out of scope

- `EDITED` proposal status and content editing — future ticket, which must also add the `history/` snapshot mechanism for Proposals.
- Bulk accept/reject, filtering beyond a single status filter, sorting, grouping, prioritization.
- Review statistics/analytics/trend reporting (UC-011 "Derived Knowledge").
- Downstream impact/staleness analysis (UC-010) triggered by acceptance.
- Entity, Event, Relationship proposal review — future ticket(s).
- Any GUI or CLI.
- Cross-domain review operations (INV-009).
- Reviewer authentication/authorization.
