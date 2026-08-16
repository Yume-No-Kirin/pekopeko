# KC-001: Canonical Item Storage Primitive (Knowledge Core)

- **Status**: completed (2026-08-16)

## Verification record

Implemented by qwen3-coder:30b, verified independently by Claude (not just a rerun of qwen's own report):

- Code copied into an isolated environment (not Cleo's machine) and all tests rerun independently: 16/16 pass.
- All 8 acceptance criteria checked one by one against the code, not assumed from the test suite passing.
- Round 1 review found 2 real bugs the test suite didn't catch: (a) no validation that `frontmatter["id"]`/`["domain"]`/`["type"]` match the function's own `item_id`/`domain`/`item_type` parameters — reproduced by writing an item with a deliberately mismatched frontmatter and confirming it was accepted silently; (b) `created_at` handling was inconsistent between first-write (always overwritten with wall-clock time) and update (kept if present) — reproduced by passing an explicit `created_at` on first write and confirming it was discarded. Both were sent back to qwen3-coder:30b for a fix round.
- Round 2: both bugs fixed, with new regression tests for each (mismatch cases, explicit `created_at` preserved on both first-write and update). Re-verified independently: reran the exact repro scripts from round 1 against the fixed code — both now behave correctly.
- Went beyond the ticket's own test suite for acceptance criterion 7 (atomicity): patched `os.replace` to fail partway through an update and confirmed the original ACTIVE file is left completely untouched and no orphaned temp file remains — a stronger check than the ticket's own `test_atomic_write`/`test_atomic_write_behavior`, which only inspect final file content and don't simulate a failure.
- Minor, non-blocking note for whoever picks up the next ticket: `test_atomic_write_behavior` (added in the fix round) doesn't actually simulate a failure and isn't a meaningfully stronger atomicity test than the original — the atomicity guarantee itself is solid (verified above by code review + an independent simulated-failure test), just the test coverage for it in the repo is weaker than ideal. Not worth another round over.

## Objective

Implement the single most foundational primitive of the Knowledge Core: writing, reading, and versioning a canonical knowledge item on disk, following the file-based storage model decided in ADI-001 and the folder structure decided in ADI-004. Every other Phase 2/3 piece (retrieval index, relationship adjacency, proposal/review workflow, ingestion) depends on canonical items existing on disk in a well-defined, reliable format first — this ticket is that foundation, and nothing else.

## Context

- `specs/decisions/ADI-001-canonical-persistence-model.md` (Accepted): canonical knowledge is structured files, not a database. On update, the previous full version is preserved as a complete snapshot in a per-item history subfolder with `lifecycle_status: SUPERSEDED` and a pointer to what superseded it — never a diff, never git.
- `specs/decisions/ADI-004-obsidian-role.md` (Accepted): the vault root is organized as `<domain>/<item-type-plural>/`, each item has its own per-item history subfolder, frontmatter is left unabridged, and all canonical writes must be atomic (write to a temp file, then rename into place) because the same files are watched concurrently by Obsidian and the sync tool.
- `specs/decisions/ADI-007-implementation-language.md` (Accepted): implemented in Python.
- `specs/architecture/principles.md`: AP-001 (structured knowledge representation), AP-003 (provenance tracking), AP-004 (historical states preserved), AP-005 (domain boundaries enforced).
- `specs/domain/knowledge-invariants.md`: INV-003 (provenance), INV-004 (history never silently destroyed), INV-007 (temporal validity: recording time vs. claimed validity are distinguishable), INV-008 (domain isolation).
- `specs/domain/knowledge-model.md`: defines the five core item types this ticket must support as folders — Entity, Assertion, Event, Relationship, Proposal — and the frontmatter concepts (Lifecycle Status: ACTIVE/SUPERSEDED/STALE/INVALIDATED; Epistemic Status: direct/inferred/uncertain/contested; Temporal Validity: recorded time vs. claimed validity).

This ticket does **not** implement human validation (AP-002) — it is the low-level storage primitive that a future validation/proposal-acceptance ticket will call once a proposal is accepted. Calling this primitive directly is, for now, how any canonical item gets written; gating that behind the review workflow is future work (see Out of scope).

## Scope

Implement a Python module providing:

1. `write_canonical_item(vault_root, domain, item_type, item_id, frontmatter, body)` — writes or updates one canonical item.
2. `read_canonical_item(vault_root, domain, item_type, item_id)` — returns the current ACTIVE version's frontmatter (dict) and body (str).
3. `read_item_history(vault_root, domain, item_type, item_id)` — returns the list of SUPERSEDED versions, oldest first, each with full frontmatter and body.

### File layout (exact contract)

```
<vault_root>/<domain>/<item_type_plural>/<item_id>/<item_id>.md      # current ACTIVE version
<vault_root>/<domain>/<item_type_plural>/<item_id>/history/<ISO8601-timestamp>--v<n>.md   # superseded versions, full snapshots
```

- `domain` ∈ {PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING} (per AP-005 / INV-008).
- `item_type_plural` ∈ {entities, assertions, events, relationships, proposals} (per ADI-004's folder structure and `knowledge-model.md`'s five core types).
- Each `.md` file is standard YAML frontmatter (`---` delimited) followed by the markdown body.

### Required frontmatter fields

- `id` (string, stable, matches `item_id`)
- `type` (string, one of the five item types, singular form, e.g. `entity`)
- `domain` (string, one of the five domains)
- `lifecycle_status` (`ACTIVE` | `SUPERSEDED` | `STALE` | `INVALIDATED`)
- `epistemic_status` (`direct` | `inferred` | `uncertain` | `contested`)
- `version` (integer, starts at 1, increments on each update)
- `created_at` (ISO 8601 timestamp — when this specific version was written)
- `valid_from` (ISO 8601 timestamp or null — claimed validity start, per INV-007; distinct from `created_at`)
- `valid_until` (ISO 8601 timestamp or null)
- `provenance` (string or dict — free-form for this ticket, e.g. a source reference string; the full provenance model is future work, this ticket only needs the field to exist and round-trip, per INV-003)
- `superseded_by` (string or null — present only on SUPERSEDED versions, pointing to the version identifier that replaced it, e.g. `v3` or the new version's `created_at` timestamp)

### Update behavior (the core mechanism)

When `write_canonical_item` is called for an `item_id` that already has an ACTIVE file:
1. Read the current ACTIVE file's full content (frontmatter + body) unchanged.
2. Determine the new version number (`n+1`) and a timestamp for the history filename.
3. Write that unchanged full previous content into `history/<timestamp>--v<n>.md`, with its `lifecycle_status` rewritten to `SUPERSEDED` and `superseded_by` set to point at the new version.
4. Atomically write the new content (`lifecycle_status: ACTIVE`, `version: n+1`) to the main `<item_id>.md` file.

Both writes (steps 3 and 4) must be atomic: write to a temp file in the same directory, then `os.replace()` (or equivalent) into place. Never write directly to the target path.

When no ACTIVE file exists yet for that `item_id`: create the folder structure and write version 1 directly as ACTIVE, no history entry.

## Requirements

- Python only (ADI-007). `pyyaml` may be used for frontmatter parsing/writing — no other new dependency without a stated reason.
- All directory creation (domain folder, item-type folder, per-item folder, history subfolder) must happen automatically as needed — never require them to pre-exist.
- Missing or invalid required frontmatter fields must raise a clear, typed validation error (not a silent write of a malformed file).
- No use of git anywhere in the implementation (per ADI-001 — this was an explicit, firm decision; do not reintroduce it).
- Must not depend on Obsidian being installed, running, or having any cache (per ADI-004).

## Constraints

- No database of any kind (SQLite or otherwise) in this ticket — that is ADI-002's retrieval index, a separate future ticket.
- No relationship-traversal logic — that is ADI-003, a separate future ticket.
- No network calls, no AI/LLM calls.

## Files/modules concerned

Suggested layout (adjust if a clearer structure emerges during implementation, but keep it a single, self-contained module for this ticket):
- `knowledge_core/storage.py` — the three functions above.
- `knowledge_core/__init__.py`
- `tests/knowledge_core/test_storage.py`

## Dependencies

None — this is the first ticket. It does not depend on any other ticket.

## Acceptance criteria

1. Writing a new item creates `<domain>/<item_type_plural>/<item_id>/<item_id>.md` with `lifecycle_status: ACTIVE`, `version: 1`, and no history folder needs to exist yet.
2. Writing an update to an existing item: the previous full content is moved into `history/<timestamp>--v<n>.md` with `lifecycle_status: SUPERSEDED` and a `superseded_by` pointer to the new version; the main file is overwritten atomically with `lifecycle_status: ACTIVE` and `version` incremented by 1.
3. `read_canonical_item` returns the current ACTIVE version's parsed frontmatter (as a dict) and body (as a string).
4. `read_item_history` returns all SUPERSEDED versions in chronological order (oldest first), each with full frontmatter and body — not diffs.
5. Calling `write_canonical_item` with missing required frontmatter fields raises a clear validation error and writes nothing to disk.
6. Three sequential updates to the same item produce exactly 2 history entries, correctly ordered, each pointing to the version that superseded it.
7. No file is ever partially written: writes go to a temp file in the same directory first, then an atomic rename.
8. `grep -r "git" ` over the implementation shows no use of git tooling/libraries for historization.

## Testing requirements

`pytest` unit tests covering every acceptance criterion above. Use `tmp_path` (or equivalent pytest temp-directory fixture) as `vault_root` — tests must never touch a real Obsidian vault or any path outside the test's own temp directory. Include at least:
- A test for first-write (no prior ACTIVE file).
- A test for update (one prior ACTIVE file → history entry created correctly).
- A test for 3 sequential updates (2 history entries, correct order and pointers).
- A test for a missing required field raising a validation error and not writing anything.
- A test asserting the write is atomic (e.g. verify a temp file naming pattern is used, or that no partial file is ever left behind on a simulated failure mid-write — whichever is more practical to test).

## Out of scope

- Retrieval index (ADI-002) — separate future ticket.
- Relationship adjacency / traversal (ADI-003) — separate future ticket.
- Proposal / human-validation workflow (AP-002) — this ticket writes items directly; gating writes behind review is future work.
- Async task orchestration (ADI-005).
- Any GUI or CLI.
- Any AI/LLM ingestion or extraction logic.
- Domain/item-type folder *naming* changes — the five domains and five item types are fixed inputs for this ticket, not something to redesign.
