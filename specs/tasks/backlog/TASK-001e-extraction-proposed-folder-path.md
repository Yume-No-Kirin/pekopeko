# TASK-001e: Extraction-Proposed Folder Path Segments (Assertions)

- **Status**: backlog

## Objective

Give the extraction LLM a way to propose the initial folder-path segments a reviewer sees
pre-filled in TASK-014's folder-path builder, before any human edit — the same "chemin proposé"
shown in `pekopeko-workflow.html`/`pekopeko-proposal-detail.html` (e.g.
`mythologie/japonaise/créatures/kitsune-transformation`). Per ADI-012 (Accepted, confirmed by
Cleo 2026-09-04), this field is proposed by the LLM, not left empty by default — but it must
degrade to an empty list cleanly wherever the provider doesn't supply one, so this ticket never
becomes a hard blocker for TASK-014.

Extends TASK-001 (`completed`) additively — same posture already used by TASK-001a
(`provider_model`/`provider_temperature`/etc.), TASK-001b (`events`), TASK-001c (zero-output
guard) and TASK-001d (duplicate-detection fix): no change to `ingest_source`'s public signature,
new field defaults to an empty list wherever absent, fully backward-compatible with every
Proposal already on disk.

**Deliberate deviation from the TASK-001a/b/c/d pattern**: those four satellites all touched
`ingestion/` *and* `extraction/` symmetrically, because both pipelines fed GUI screens
(TASK-009/010/011) that displayed assertion **and** entity/event/relationship data side by side.
This ticket is **ingestion-only** (Assertions). TASK-014, the ticket this satellite supports, is
scoped assertion-only (same MVP boundary as TASK-010/011/013); ADI-012 itself says
entity/event/relationship canonical writers don't adopt the new folder layout until TASK-005/012
land. Adding `proposed_path_segments` to `extraction/`'s `ExtractedEntity`/`ExtractedEvent`/
`ExtractedRelationship` now would be a field with no consumer — speculative code AGENTS.md's
"Simplicity First" rules out ("No features beyond what was asked, no abstractions for single-use
code"). Extraction gets its own satellite if/when TASK-012 needs this.

## Binding context (references, not duplicated here)

- **ADI-012** (folder-path-organization, Accepted): the decision this ticket implements one half
  of — path segments physically relocate the canonical file, proposed by the LLM, degrading to
  empty.
- **TASK-001** (`specs/tasks/completed/TASK-001-data-ingestion.md`, `completed`): the pipeline
  this ticket extends. `ingest_source`'s signature is not changed.
- **TASK-001a** (`specs/tasks/completed/TASK-001a-extraction-provenance-metadata.md`,
  `completed`): the closest precedent for this ticket's shape — adds optional provider-reported
  fields to the Proposal's frontmatter, `null`/absent-safe if the provider doesn't supply them.
  Follow the same "no signature change, no new required field" discipline.
- `src/app/ingestion/providers/base.py:9-12` (`ExtractedAssertion` — `text`, `epistemic_status`)
  and `:15-20` (`ExtractionResult`) — the dataclasses this ticket extends.
- `src/app/ingestion/providers/ollama_provider.py:87-120` (`_build_extraction_prompt`) and
  `:122-145` (`_parse_assertions`) — the prompt/parse pair this ticket extends. Current format is
  plain-text, one assertion per line: `<epistemic_status>: <assertion_text>`.
- `src/app/ingestion/storage.py:156-194` (proposal-writing function, frontmatter dict built at
  `:164-182`) — where the new field is added to the Proposal's frontmatter.
- TASK-014 (`specs/tasks/backlog/TASK-014-folder-path-organization.md`, `backlog`): the consumer
  of this field. TASK-014 must not depend on this ticket being implemented first (see V1 scope
  decisions) — same non-blocking-satellite posture TASK-011 already used for TASK-001a/TASK-001b.

## Scope

1. `ExtractedAssertion` (`providers/base.py`) gains
   `proposed_path_segments: list[str] = field(default_factory=list)` (needs `from dataclasses
   import dataclass, field` — currently only `dataclass` is imported).
2. `OllamaProvider._build_extraction_prompt` asks the model to optionally propose a short folder
   path per assertion, appended to the existing line format with a new delimiter so the format
   stays backward-parseable:
   ```
   <epistemic_status>: <assertion_text> | <segment1>/<segment2>/...
   ```
   The ` | <path>` suffix is optional in both the prompt's instructions and the parser — a line
   with no `|` produces `proposed_path_segments: []`, identical to today's behavior.
3. `OllamaProvider._parse_assertions` splits each line on `' | '` first (at most once), applies
   the existing `<epistemic_status>: <assertion_text>` parse to the first part, and — only if a
   second part is present and non-empty — splits it on `/` into `proposed_path_segments`,
   trimming each segment and dropping empty ones. No exception is raised for a missing or
   malformed path suffix (unlike the existing hard failure on a missing `epistemic_status`,
   `_parse_assertions:143-145` — this field is optional, not quality-gated the same way).
4. `ingestion/storage.py`'s proposal-writing function threads `assertion.proposed_path_segments`
   into the frontmatter dict (`:164-182`) as `'proposed_path_segments': assertion.proposed_path_segments`
   (empty list, never omitted — keeps the frontmatter shape uniform across every Proposal,
   consistent with how `valid_until: None` is already always present rather than omitted).
5. No change to `_validate_frontmatter`'s required-fields list (`:190-191`) — this field is
   always present (possibly empty), so it doesn't need to join the required-fields check, but it
   is also not optional-and-absent the way TASK-001a's fields are (those use `None`, this uses
   `[]`) — call this out in the ticket's own tests rather than silently picking one.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- No validation that a proposed segment is a "good" folder name (no length cap, no character
  allow-list enforced server-side) — ADI-012's naming convention is documented, not enforced,
  here; TASK-014's own edit path is where a reviewer would notice and fix a bad LLM suggestion
  before it's ever written to disk.
- No prompt tuning/quality iteration beyond "ask for it, parse it if present" — same V1 posture
  TASK-001's original prompt already took for epistemic status; this is not a ticket about
  extraction quality.
- `extraction/` (entity/event/relationship) is explicitly untouched — see Objective's deviation
  note.

## Requirements

Python only, no new dependency. Same testing discipline as TASK-001a/b/c/d: `pytest`, `tmp_path`,
mocked provider responses (no real Ollama call in the default test suite).

## Constraints

- No change to `ingest_source`'s public signature.
- No change to `ExtractedAssertion.text`/`.epistemic_status` or their existing validation.
- `proposed_path_segments` is always a list (possibly empty), never `None`, never omitted from
  the written frontmatter.
- Existing Proposals on disk without this field remain readable — this ticket only affects
  frontmatter *written* going forward; no migration.

## Files/modules concerned

- `src/app/ingestion/providers/base.py` (`ExtractedAssertion`)
- `src/app/ingestion/providers/ollama_provider.py` (`_build_extraction_prompt`, `_parse_assertions`)
- `src/app/ingestion/storage.py` (proposal frontmatter dict)
- New/updated tests in `src/tests/ingestion/` mirroring TASK-001a's test structure: prompt
  includes the new instruction; parser handles a line with a path suffix, a line without one, a
  line with an empty suffix (`| `), and a line with a malformed suffix (extra empty segments from
  doubled slashes) without raising; frontmatter written contains `proposed_path_segments` as a
  list in every case.

## Dependencies

TASK-001 (`completed`) and ADI-012 (Accepted). Independent of TASK-003/`extraction/` (untouched
by this ticket, see Objective). TASK-014 does not depend on this ticket for its own
implementability (non-blocking, degrades to an empty list) — but TASK-014's acceptance criteria
about the pre-filled path in the mockup are only fully satisfied once this ticket also lands.

## Acceptance criteria

1. `ExtractedAssertion` has a `proposed_path_segments: list[str]` field defaulting to `[]` when
   not supplied by a caller.
2. The extraction prompt sent to Ollama includes an instruction and example for the optional
   ` | <segment1>/<segment2>/...` suffix.
3. A response line with a valid `| <path>` suffix produces an `ExtractedAssertion` whose
   `proposed_path_segments` matches the slash-split, trimmed, non-empty segments.
4. A response line with no `|` suffix produces `proposed_path_segments: []` — no regression from
   today's parsing for a line already in the old format.
5. A response line with an empty or whitespace-only suffix after `|` produces
   `proposed_path_segments: []` rather than a list containing empty strings.
6. A malformed suffix (e.g. leading/trailing/doubled slashes) never raises — empty segments are
   silently dropped, non-empty ones kept in order.
7. The `epistemic_status`/`text` parsing and its existing validation (invalid status still
   raises `ValueError`) are unchanged by the presence or absence of a `|` suffix.
8. The Proposal frontmatter written by `ingest_source` for a batch of assertions with and without
   proposed paths always includes `proposed_path_segments` as a list (never omitted, never
   `None`).
9. `ingest_source`'s public signature is unchanged (regression check by direct comparison).

## Testing requirements

`pytest`, `tmp_path`, mocked Ollama HTTP responses (no real network call), covering AC1-9.
Project-wide bar: at least 80% coverage on every file touched.

## Out of scope

- `extraction/` (entity/event/relationship path-segment proposals) — future ticket alongside
  TASK-005/TASK-012 if needed.
- Prompt quality tuning beyond the minimal instruction/example addition.
- Server-side validation/sanitization of proposed segment names — left to TASK-014's reviewer
  edit path.
- Any consumption of this field — that's TASK-014's own scope.
