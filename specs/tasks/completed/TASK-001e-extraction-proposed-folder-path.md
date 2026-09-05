# TASK-001e: Extraction-Proposed Folder Path Segments (Assertions)

- **Status**: completed (implemented 2026-09-04; amended the same day per ADI-014, see
  "Amendment" section below)

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
- Prompt quality tuning beyond the minimal instruction/example addition. **Superseded in part by
  the Amendment below** — this ticket's original "no prompt tuning" posture was overtaken by the
  discovery that the optional suffix was never used in practice, not by a change in ambition.
- Server-side validation/sanitization of proposed segment names — left to TASK-014's reviewer
  edit path.
- Any consumption of this field — that's TASK-014's own scope.

## Amendment (2026-09-04, same-day production verification): mandatory path, ADI-014

Verifying this ticket in production (re-ingesting the real vault note `Plot Tatouages.md`
against `qwen2.5:7b`) found the optional `| <path>` suffix (Scope items 2-3 above) never used in
practice: the raw Ollama response was inspected directly (not just parsed output) across two
separate real runs — 0 of 39 lines, then 0 of 79 lines, ever carried it. Cleo's decision, recorded
as **ADI-014** (amends ADI-012, `specs/decisions/ADI-014-mandatory-extraction-proposed-path.md`):
every proposal must have a dedicated path — the field is no longer allowed to silently degrade to
empty for `OllamaProvider`.

**This supersedes AC4 and AC5 below as originally written** (a missing/empty `|` suffix producing
`proposed_path_segments: []`) — see ADI-014 for the full decision and rationale. What changed,
additively, on top of everything else in this ticket (Scope items 1-5, the original `|` suffix
mechanism, and AC1/AC2/AC3/AC6/AC7/AC8/AC9 are all unchanged and still hold):

- `OllamaProvider._ensure_path_segments` (new): after parsing, for any assertion whose
  `proposed_path_segments` is still empty, calls `_propose_path_with_retry` — up to
  `PATH_PROPOSAL_MAX_ATTEMPTS` (3) dedicated per-assertion Ollama calls (assertion text + full
  source note content + existing vault folder paths as context), retried on empty/malformed
  response or network error, falling back to `FALLBACK_PATH_SEGMENTS = ["uncategorized"]` if all
  attempts fail. Never raises — ingestion is never hard-blocked by a stubborn path proposal.
- `OllamaProvider._propose_path`/`_build_path_prompt` (new): the dedicated per-assertion call and
  its prompt.
- `ingestion/storage.py::scan_existing_assertion_folders` (new): full existing folder paths under
  `<domain>/assertions/`, an independent reimplementation of `review/storage.py`'s
  `scan_organization_folders` (module-independence discipline, TASK-002) returning `"/"`-joined
  paths rather than depth-grouped segment names.
- `ingestion/pipeline.py`: `provider.extract()`'s `context` dict gains `vault_root`/`domain` keys
  (additive; `ingest_source`'s own public signature is still unchanged, AC9 still holds) so
  `OllamaProvider` can call `scan_existing_assertion_folders`.

**Tests updated in place** (`src/tests/ingestion/test_ollama_provider.py`): the two tests that
asserted AC4/AC5's original "missing/empty suffix → `[]`" behavior were rewritten to assert the
new mandatory-path-proposal-call behavior instead
(`test_extract_no_path_suffix_triggers_path_proposal_call`,
`test_extract_empty_path_suffix_triggers_path_proposal_call`). Six new tests added:
`test_extract_only_calls_path_proposal_for_assertions_missing_one` (mixed batch),
`test_path_proposal_retries_then_succeeds`,
`test_path_proposal_falls_back_after_exhausting_retries`,
`test_path_proposal_swallows_errors_during_retry_then_falls_back`,
`test_extract_passes_existing_vault_folders_to_path_prompt`, plus
`test_scan_existing_assertion_folders_empty_when_missing`/
`test_scan_existing_assertion_folders_returns_full_paths` and
`test_ingest_source_passes_vault_root_and_domain_to_provider_context` in
`src/tests/ingestion/test_pipeline.py`. AC1/AC2/AC3/AC6/AC7/AC8/AC9's original tests are
unchanged and still pass.

## Amendment 2 (2026-09-04, same day): mandatory nomenclature + cross-proposal context, ADI-015

A real screenshot of Amendment 1's own verification run showed the model's raw path segments
were messy: HTML entities leaking through (`&amp;`), accented French left as-is, two concepts
glued into one segment (`enjeux&themes`, `coopération_vs_pouvoir_solitaire`,
`symbiose-vs-domination`), multi-word segments joined by `_`/`-` instead of split into their own
folder levels. Cleo also asked for the existing-folder context to include not-yet-accepted
Proposals' paths and paths already chosen earlier in the same extraction batch. Recorded as
**ADI-015** (amends ADI-014, `specs/decisions/ADI-015-path-nomenclature-and-cross-proposal-context.md`).

What changed, additively, on top of Amendment 1:

- `OllamaProvider._normalize_path_string` (new): every raw path string, from either the inline
  suffix or the dedicated second call, is now HTML-unescaped, split into single-word tokens on
  `/`, `&`, whitespace, `_` and `-`, accent-stripped (including `œ`/`æ`), lowercased, and stripped
  of any remaining non-`[a-z0-9]` character; a small connector/stopword set (`vs`, `et`, `and`,
  `de`, `du`, `des`, `la`, `le`, `les`, `l`) is dropped. Splitting happens *before* stopword
  filtering specifically so a connector glued in with underscores (`cooperation_vs_pouvoir`) is
  still caught.
- `_build_extraction_prompt` (item 6) and `_build_path_prompt` gain explicit nomenclature rules
  and a worked before/after example, to reduce how often the normalizer has to do real work — it
  remains the actual guarantee, not the prompt.
- `storage.py::scan_proposed_path_segments` (new): paths already proposed by Proposals with
  `proposal_status` `PROPOSED`/`EDITED` elsewhere in the domain, read from frontmatter (a small
  private `_read_frontmatter` helper added alongside it, tolerant of malformed proposal files).
  `_ensure_path_segments`'s `existing_folders` is now the union of this and
  `scan_existing_assertion_folders`.
- `_ensure_path_segments` also accumulates in-memory: each assertion's resolved path is appended
  to `existing_folders` before the next assertion in the same batch is resolved, so a note's own
  later assertions can reuse a path an earlier one in the same call just chose.

**Tests added** (`src/tests/ingestion/test_ollama_provider.py`): 9 unit tests on
`_normalize_path_string` directly (accents, ligatures, HTML entities, `&`/`vs` splitting,
underscore/hyphen compounds, stopword dropping, special characters, and the exact dirty strings
from Cleo's screenshot), 2 integration tests confirming normalization applies at both call sites,
1 within-batch accumulation test, 1 merged-scan-sources test, 2 prompt-content tests.
`src/tests/ingestion/test_pipeline.py`: 6 new tests for `scan_proposed_path_segments` (empty,
status filtering, missing/empty segments, malformed proposal files, dedup).

## Verification record

- `pytest src/tests/ingestion/ --cov=src/app/ingestion --cov-report=term-missing`: 96 passed, 2
  failed — both preexisting and unrelated (`test_comprehensive.py::test_acceptance_criteria_compliance`
  and `test_pipeline.py::test_import_isolation`, both confirmed via `git stash`/`git stash pop` to
  fail identically on the pre-TASK-001e code). Coverage on every file this ticket (original +
  both amendments) touched: `providers/base.py` 100%, `providers/ollama_provider.py` 99% (1
  preexisting untested line, `_parse_assertions`'s missing-status raise, predates this ticket),
  `storage.py` 98% (2 preexisting untested lines, both predate this ticket) — well above the
  project's 80% bar.
- 9 acceptance criteria (AC1-9) verified one by one via the tests listed above and in the original
  ticket text; AC4/AC5 verified against their *amended* form (mandatory path, not `[]`) per the
  Amendment 1 section, not their original wording.
- Manual, real (non-mocked) end-to-end reproduction, three separate real runs against the actual
  vault note `Plot Tatouages.md` (`A:\DATA\OBSIDIAN\Pekopeko\Pekopeko\Plot Tatouages.md`) via the
  real running Flask API + real Ollama (`qwen2.5:7b`):
  1. Original mechanism (optional suffix only): `proposed_path_segments: []` end-to-end for every
     one of 79 written Proposals (0/79 lines used the suffix, root-caused by inspecting the raw
     Ollama response directly).
  2. After Amendment 1 (mandatory path): 80 Proposals, 0 empty, 0 fell back to `["uncategorized"]`,
     67 distinct real paths across 80 assertions, ~75s total (vs. ~50s before). This run is the
     one whose screenshot triggered Amendment 2 — segments contained `&amp;`, accents, and
     multi-word compounds.
  3. After Amendment 2 (mandatory nomenclature + cross-proposal context): 81 Proposals, 0 empty,
     0 fallback, **0 segments containing anything outside `[a-z0-9]`** (checked programmatically
     against every segment in every written Proposal, not sampled), 38 distinct paths across 81
     assertions (down from 67/80 in run 2 - direct evidence the cross-proposal + in-batch context
     sources measurably improved folder-name reuse, not just formatting), ~105s total. One
     transient run of the raw extraction call failed on a single malformed model output line
     (missing epistemic status) at temperature 0.7 - reproduced the exact same prompt a second
     time immediately after and got a clean response, confirming this is pre-existing sampling
     variance (existed before this ticket, governed by ADI-011's existing zero-output/malformed-
     output-is-a-failure contract) and not a regression introduced by the nomenclature prompt
     changes.
  Frontmatter inspected by eye on multiple written Proposal files across all three runs to
  confirm `proposed_path_segments` is a real YAML list, correctly UTF-8 (an initial "corruption"
  concern during manual testing was confirmed to be a terminal-display artifact only, not real
  data corruption, by writing segments to a file and reading it back).
- Same limitation as every previous ticket in this project: verification done by the same
  session/model that implemented the change, not by a second independent reviewer.
