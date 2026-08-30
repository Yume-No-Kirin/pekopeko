# TASK-003: Entity, Event and Relationship Extraction Module (V1)

- **Status**: completed

## Objective

Implement a minimal extraction pipeline for entities, events, and relationships from source material. Given a single Markdown (.md) source file, preserve the source, extract structured knowledge elements via a pluggable LLM provider, and write them as review-pending Proposal items. Mirrors TASK-001's pipeline shape (source preservation, pluggable provider extraction, Proposal-only output) to support additional knowledge types -- entities, events, relationships -- beyond assertions; implemented independently of TASK-001's code, per the Constraints below.

Implements SOURCE -> AI INTERPRETATION/EXTRACTION -> PROPOSAL from specs/domain/knowledge-model.md for entities, events, and relationships. Stops at PROPOSAL -- human review (accept/reject into canonical) is a separate future ticket.

This ticket is self-contained: independent of any other ticket or existing code, including knowledge_core/storage.py. It implements its own minimal file-writing logic rather than importing another module (explicit product decision). It must still conform to the Accepted ADRs below, regardless of which code implements them.

## Binding context (references, not duplicated here)

- specs/domain/knowledge-model.md -- conceptual flow and definitions of Source, Assertion, Entity, Event, Relationship, Proposal.
- ADI-001 (canonical-persistence-model, Accepted): one structured file per item (YAML frontmatter + body), domain-scoped directories, stable explicit IDs, no database, no git, atomic writes required.
- ADI-003 (relationship-model, Accepted): canonical relationships are structured records that explicitly name their endpoints by stable item IDs, plus their type, temporal validity, and provenance. This ticket only ever produces Proposals, not canonical relationships, so a proposed relationship's `endpoints` reference the `proposal_id`s of its co-extracted Entity/Event proposals (or an existing canonical item's stable id, if the source refers to something already accepted) -- resolution to final canonical stable IDs happens in the future review ticket, once/if those endpoints are themselves accepted.
- ADI-004 (obsidian-role, Accepted): vault layout <domain>/<item-type-plural>/<item-id>/<item-id>.md, with folders entities/assertions/events/relationships/proposals, plus the sources/ folder already established as a sixth per-domain folder by TASK-001 (for preserved raw source material, required by CAP-002 and UC-001). This ticket writes only into the existing sources/ and proposals/ folders -- entities/, events/, and relationships/ stay reserved for canonical items created by a future review ticket (mirroring how TASK-002 only creates assertions/ files upon acceptance), never written here (see INV-001/CAP-002 and Constraints).
- ADI-005 (sync-vs-async, Accepted), Rule 1: extraction is async, runs as a background task; result is a Proposal added to the review queue; user never blocked. In-flight task state must be persisted locally, outside the vault, per-device, recoverable.
- ADI-007 (implementation-language, Accepted): Python.
- ADI-008 (llm-provider-architecture, Accepted): extraction must go through a pluggable provider interface (extract(text, context) -> ExtractionResult); pipeline code must never import/reference a provider SDK directly; active provider chosen by local config. No default provider mandated (a local Ollama endpoint is suggested as simplest).
- specs/domain/knowledge-invariants.md:
  - INV-001: extraction must never write directly to canonical status -- only Proposal items.
  - INV-002 / INV-016: extracted entities/events/relationships must carry epistemic_status distinguishing them from directly-sourced fact, plus provenance to the exact source.
  - INV-003: every Proposal traceable to its source and the processing step that produced it.
  - INV-007: distinguish when a source was ingested from when its content claims to be true/applicable.
  - INV-019: a failed extraction must not corrupt the source or leave a partially-written Proposal file -- must leave inspectable, honest failure state.
  - INV-020: re-extracting the same source content must not blindly create duplicate proposals.
- specs/product/capabilities.md, CAP-002: store source materials separately from extracted knowledge; all canonical knowledge human-reviewed; AI-generated info cannot auto-become canonical.
- specs/product/use-cases.md, UC-001 (Novel Ingestion), UC-007 (Multimodal Ingestion), UC-016 (Duplicate/Repeated Ingestion) -- framing use cases.

## Scope

Implement a Python package providing an ingestion pipeline that:

1. Reads a single Markdown source file from a given path.
2. Preserves that source as a canonical-compatible file under the vault.
3. Detects exact-duplicate re-ingestion (by content hash) and skips reprocessing if already ingested.
4. Calls a pluggable LLM provider to extract a list of entities, events, and relationships from the source text.
5. Writes each extracted entity/event/relationship as a Proposal file with proposal_status: PROPOSED.
6. Tracks the state of each extraction attempt (pending/running/completed/failed) in local, non-canonical storage outside the vault.

### V1 scope decisions

- Entity, Event, and Relationship extraction only. Assertion extraction is covered by TASK-001.
- Only .md sources in V1, but reading is behind an extensible reader registry keyed by file extension -- adding a new format later means adding a reader, not modifying the pipeline.
- domain is passed explicitly to the pipeline, never inferred (INV-008/AP-005).
- Exactly one concrete LLM provider required (a local Ollama HTTP endpoint recommended), reached only through the extract() interface -- never called directly from pipeline code.
- Duplicate detection is exact-content-hash only. Detecting a *modified* re-ingestion of a previously-seen source is out of scope.
- Task state is minimal: one local record per attempt with a status field -- not a general-purpose task queue/orchestrator.
- A proposed relationship's `endpoints` reference the `proposal_id`s of co-extracted Entity/Event proposals (or an existing canonical item id, if applicable) -- not yet resolved to final canonical stable IDs, since the endpoints themselves may not be canonical until reviewed. Full canonical endpoint resolution is future work for the entity/event/relationship review ticket (see TASK-002, which already scopes entity/event/relationship proposal review out for V1).

### File layout (exact contract)

<vault_root>/<domain>/sources/<source_id>/<source_id>.md
<vault_root>/<domain>/proposals/<proposal_id>/<proposal_id>.md

- Source file is written as sources/<source_id>/<source_id>.md with:
  - item_type: source
  - domain: <domain>
  - source_id: <source_id> (stable ID from the content hash)
  - created_at: <timestamp>
  - source_path: <path> (relative path in vault)
  - source_format: markdown
  - content: <content> (the full source content)

- Proposal files are written as proposals/<proposal_id>/<proposal_id>.md with:
  - item_type: proposal
  - domain: <domain>
  - created_at: <timestamp>
  - proposal_status: PROPOSED
  - provenance.source_id: <source_id> (link back to the source)
  - provenance.extraction_provider: <provider_name> (for tracing the processing step)
  - proposed_item_type: entity|event|relationship (indicating what kind of item is proposed)
  - epistemic_status: direct|inferred|uncertain|contested (as appropriate for the extracted item type)
  - valid_from / valid_until: ISO 8601 timestamp or null (claimed validity of the content, distinct from created_at, per INV-007)
  - entity_type: free text, e.g. person|place|organization|object|other -- present only when proposed_item_type: entity
  - starts_at / ends_at: ISO 8601 timestamp or null -- present only when proposed_item_type: event
  - relationship_type: free text describing the semantic connection -- present only when proposed_item_type: relationship
  - endpoints: list of at least 2 identifiers (a co-extracted proposal_id or an existing canonical item id) that the relationship connects -- present only when proposed_item_type: relationship (per ADI-003)

### V1 extraction type details

- Entities are distinct, identifiable objects or concepts with a stable identifier. They can be people, places, organizations, objects, or other discrete items.
- Events are occurrences or actions that take place within a specific time frame. They may be personal activities, historical occurrences, fictional happenings, or any temporally situated action or state change.
- Relationships describe connections between two or more knowledge elements (entities, events, or other relationships).

## Requirements

- Python only (ADI-007). `pyyaml` for frontmatter -- no other new dependency without a stated reason.
- All directory creation (domain folder, sources/ and proposals/ folders, per-item folder) happens automatically as needed.
- Missing or invalid required frontmatter fields (including the type-specific proposal fields above) raise a clear, typed validation error before any file is written.
- No use of git anywhere in the implementation (ADI-001).
- Must not depend on Obsidian being installed or running.
- All writes to sources/ and proposals/ files are atomic (write to a temp file in the same directory, then os.replace() or equivalent).

## Constraints

- No EDITED status -- only PROPOSED -> ACCEPTED and PROPOSED -> REJECTED.
- No history/ snapshot subfolder for proposals in this ticket.
- No database -- plain files only.
- No GUI or CLI required (Python function entry points suffice).
- No dependency on ingestion/ (TASK-001), knowledge_core/, or any other existing module -- only the shared file/frontmatter contract. Tests build their own fixture Source files.
- No cross-domain extraction (INV-008).
- No authentication/authorization -- extractor_id is trusted as given.

## Files/modules concerned

Suggested layout (adjust if a clearer structure emerges, but keep module boundaries matching the interfaces above):

- extraction/providers/base.py -- ExtractedEntity, ExtractedEvent, ExtractedRelationship, ExtractionResult, Provider protocol.
- extraction/providers/ollama_provider.py -- concrete OllamaProvider.
- extraction/readers/base.py -- SourceReader protocol and the registry.
- extraction/readers/markdown_reader.py -- concrete markdown reader.
- extraction/storage.py -- atomic write helpers for Source and Proposal files, frontmatter validation.
- extraction/task_state.py -- task state record read/write.
- extraction/pipeline.py -- orchestration: extract_source(vault_root, domain, source_path, provider) -> ExtractionResult.
- tests/extraction/ -- mirroring the modules above.

## Dependencies

None. Independent of any other ticket or existing module in this repository.

## Acceptance criteria

1. Ingesting a .md source file produces a Source file at <domain>/sources/<source_id>/<source_id>.md with all required frontmatter fields, and one Proposal file per extracted entity/event/relationship at <domain>/proposals/<proposal_id>/<proposal_id>.md with all required frontmatter fields -- including proposal_status: PROPOSED, provenance.source_id pointing at the Source file just created, and the type-specific fields required for its proposed_item_type (entity_type for entities; starts_at/ends_at for events; relationship_type and endpoints for relationships).
2. No pipeline code (extraction/pipeline.py, extraction/storage.py, extraction/readers/*) imports or references a concrete LLM SDK/HTTP client directly -- only extraction/providers/ollama_provider.py (or equivalent) does. Verifiable by static inspection.
3. Ingesting the exact same source file a second time (same content, same domain) creates no new Source file or Proposal files -- the pipeline detects the existing source_id and returns a result indicating a skipped duplicate (INV-020).
4. If the provider's extract() call raises/fails (simulated in a test): no partial or corrupt Source or Proposal file is left on disk, the original input file is untouched, and the task state record reflects status: failed with a non-null error.
5. Adding a second registered reader (e.g. a trivial .txt reader used only in a test) requires no changes to extraction/pipeline.py -- only a new reader module plus a registry entry.
6. Swapping the configured provider for a second, minimal test/fake provider (implementing the same Provider protocol) requires no changes to extraction/pipeline.py -- only local configuration.
7. Every extracted entity/event/relationship's Proposal frontmatter includes an epistemic_status value from {direct, inferred, uncertain, contested} -- never omitted, never silently defaulted to something implying certainty.
8. All Source/Proposal writes are atomic: verified either by inspecting for temp-file-then-rename behavior in code, or by simulating a failure mid-write and confirming no partial file is left behind.
9. `grep -r "git"` over the `extraction/` implementation shows no use of git tooling/libraries for historization.

## Testing requirements

pytest unit tests covering every acceptance criterion above. Use tmp_path (or equivalent) as vault_root and a local temp directory for task state -- tests must never touch a real Obsidian vault or write anything outside their own temp directories. The LLM provider must be mocked/faked in tests (no real network calls) except, optionally, one clearly-marked integration test skipped by default. Include at least:
- A first-ingestion test asserting the full file layout and frontmatter contract (Criterion 1).
- A type-specific-fields test verifying entity_type / starts_at+ends_at / relationship_type+endpoints are present and correctly populated for each proposed_item_type (Criterion 1).
- A static-inspection or import-graph test for provider isolation (Criterion 2).
- A duplicate-ingestion test (Criterion 3).
- A simulated provider-failure test (Criterion 4).
- A second-reader extensibility test (Criterion 5).
- A second-provider extensibility test (Criterion 6).

## Out of scope

- Assertion extraction -- covered by TASK-001.
- Proposal review/accept/reject/edit workflow (AP-002) -- future ticket, produces canonical knowledge from these proposals.
- Resolving relationship endpoints to final canonical stable item IDs -- a proposed relationship's endpoints reference other proposals (or existing canonical items) from the same extraction; canonical endpoint resolution happens in the future entity/event/relationship review ticket.
- Any file format other than .md (PDF, audio, video, images, web pages -- UC-007) -- future ticket(s), enabled by the reader registry this ticket establishes.
- Semantic/near-duplicate detection, staleness detection on source modification (UC-003, richer parts of UC-016).
- A real asynchronous task orchestrator/queue -- this ticket only defines the task-state record shape, not a scheduler.
- Any GUI or CLI.
- A second or third concrete LLM provider beyond the one required for V1.
- Consolidating this module's storage logic with knowledge_core/storage.py or any other existing module.

## Implementation notes

Implemented at `src/app/extraction/` (`errors.py`, `frontmatter.py`, `storage.py`,
`task_state.py`, `readers/base.py`, `readers/markdown_reader.py`,
`providers/base.py`, `providers/ollama_provider.py`, `pipeline.py`), tests at
`src/tests/extraction/` (41 tests, 100% line coverage of `src/app/extraction`).
Independent of `app.ingestion` and `app.review` (no imports; only the on-disk
frontmatter contract is shared per ADI-001/ADI-004), following `app/review/`'s
more mature pattern rather than `app/ingestion/`'s: typed exceptions
(`errors.py`), a fixed atomic-write helper (cleans up the `.tmp` file if
`os.replace()` itself fails -- the real bug TASK-002's verification found and
fixed in `app/ingestion/storage.py`'s original version), and small path-builder
helpers in `storage.py`.

**Frontmatter field names follow this ticket's own "File layout (exact
contract)" section literally** (`item_type`, `source_id`, `source_path`,
`content` for the Source file; no separate `id` field on Proposals), which
differs from TASK-001's field names (`type`, `id`, `original_filename`,
`content_hash`) -- the two tickets specify different contracts and neither
references the other's code, so this divergence is expected, not an error.

**Relationship endpoint resolution** (not spelled out in code by the ticket):
`ExtractedEntity`/`ExtractedEvent` carry a provider-assigned `local_id`
scoped to one extraction call. `pipeline.py` writes all entity then event
proposals first, building a `local_id -> proposal_id` map, then resolves each
relationship's `endpoints` through that map before writing the relationship
proposal (a string not matching any `local_id` is passed through unchanged,
treated as an existing canonical item id per the ticket's own wording).

**OllamaProvider** asks the model for a single JSON object
(`{"entities": [...], "events": [...], "relationships": [...]}`) rather than
TASK-001's line-delimited `"status: text"` format, since three item types with
different type-specific fields plus the `local_id`/`endpoints` correlation
can't be expressed in a flat line format. Parsing fails loud (raises) on
malformed JSON or an invalid `epistemic_status`, never silently defaults.

**Post-verification cleanup (2026-08-30):** `VALID_EPISTEMIC_STATUSES` was
originally defined separately in `storage.py` (a `set`) and
`providers/ollama_provider.py` (a `list`) -- same four values in both, so no
functional bug, but a latent drift risk since both were hand-maintained.
Consolidated into a single `frozenset` in `providers/base.py` (the module
that already owns the `epistemic_status` vocabulary via the `Extracted*`
dataclasses); `storage.py` and `ollama_provider.py` now both import it
instead of redefining it. Also added `test_source_id_changes_when_middle_of_content_changes`
to `test_storage.py`, explicitly demonstrating that `_generate_source_id`
hashes the *entire* source content (SHA-256 always consumes its full input;
only the resulting hex-digest string is truncated to 16 characters to keep
the id short) rather than only a prefix/suffix -- confirms duplicate
detection (AC3) is not vulnerable to two different sources sharing only a
common start/end. No production behavior changed by either point; both were
re-verified in the isolated scratch copy (41/41 tests, 100% coverage).

**Inherited characteristic (not introduced by this ticket):** duplicate
detection is existence-only on `source_id` (content hash), same as TASK-001.
If extraction fails after the Source file is already written, re-ingesting
identical content is skipped as a duplicate rather than retried, since the
pipeline cannot distinguish "already fully processed" from "source written,
extraction failed" by file existence alone. This mirrors TASK-001's accepted
behavior; changing dedup semantics was out of scope for this ticket.

## Verification record (2026-08-30)

Implemented by Claude (this session). Per this project's verification
discipline: code was copied to an isolated scratch directory (outside the
repo, `.../scratchpad/task003_verify/`) and the test suite re-run
independently there (41/41 passed, 100% coverage, matching the in-repo run),
rather than trusting the in-repo run alone. A hand-written manual
reproduction script (`manual_repro.py`, run in the isolated copy) called
`extract_source` directly and the resulting Source/Proposal files were read
back and inspected by eye -- frontmatter fields, relationship endpoint
resolution (local_id -> real proposal_id), and duplicate-skip behavior all
matched the contract. Each acceptance criterion checked individually:

- `[PASS]` AC1 (Source + one Proposal file per extracted item, all required
  frontmatter incl. `proposal_status: PROPOSED`, `provenance.source_id`, and
  type-specific fields) -- `test_first_extraction_full_contract`
  (`test_pipeline.py`) and all of `test_type_specific_fields.py` pass in both
  runs; manually confirmed by eye via `manual_repro.py`'s printed file
  contents.
- `[PASS]` AC2 (no pipeline/storage/reader code imports an LLM SDK/HTTP client
  directly) -- `test_non_provider_modules_do_not_import_llm_sdk` and
  `test_ollama_provider_only_imports_requests_lazily`
  (`test_import_isolation.py`) pass; `requests` is imported lazily inside
  `OllamaProvider.__init__` only.
- `[PASS]` AC3 (re-ingesting identical content creates no new files, returns
  `skipped_duplicate`) -- `test_duplicate_detection` (`test_pipeline.py`)
  passes, asserting the provider is called exactly once and the proposals
  directory still holds exactly the original 3 files after the second call;
  reconfirmed in `manual_repro.py`'s duplicate re-ingestion step.
- `[PASS]` AC4 (provider failure leaves no partial/corrupt file, original
  input untouched, task state `failed` with non-null `error`) --
  `test_provider_failure_handling` (`test_pipeline.py`) and
  `test_pipeline_records_failed_status_with_error` (`test_task_state.py`)
  pass. Note: the Source file is written *before* the provider call (mirrors
  TASK-001) and is intentionally left in place on provider failure -- this is
  a complete write, not a partial one; no proposal files exist.
- `[PASS]` AC5 (second reader registered without touching `pipeline.py`) --
  `test_second_reader_extensibility` (`test_extensibility.py`) registers a
  local `MockTextReader` on a freshly-built `SourceReaderRegistry`.
- `[PASS]` AC6 (second provider swapped without touching `pipeline.py`) --
  `test_second_provider_extensibility` (`test_extensibility.py`) passes a
  plain `MockProvider` class (structural `Provider` typing, no inheritance)
  directly into `extract_source`.
- `[PASS]` AC7 (`epistemic_status` always one of the 4 values, never silently
  defaulted) -- `test_write_entity_proposal_file_invalid_epistemic_status_raises`
  (`test_storage.py`) and `test_extract_raises_on_invalid_epistemic_status`
  (`test_ollama_provider.py`, LLM-response-level) both confirm a bad value
  raises rather than defaulting; every write path requires an explicit valid
  value.
- `[PASS]` AC8 (atomic writes; failure leaves no partial file) --
  `test_atomic_write_creates_file_no_leftover_tmp`,
  `test_atomic_write_cleans_up_tmp_on_replace_failure`, and
  `test_no_rollback_target_file_untouched_on_replace_failure`
  (`test_storage.py`) simulate an `os.replace()` failure via monkeypatch and
  confirm no `.tmp` file survives and the original target (if any) is
  unchanged -- using the fixed cleanup pattern from `app/review/storage.py`
  (the orphaned-`.tmp`-file bug TASK-002 found and fixed does not recur here).
- `[PASS]` AC9 (no git usage) -- `grep -rn "git" src/app/extraction/` returns
  nothing in both the working tree and the isolated copy;
  `test_no_git_usage_in_extraction_module` passes independently in both too.
- `[PASS]` Test coverage -- `pytest --cov=src.app.extraction` reports 100%
  line coverage (351/351 statements) in both the working tree and the
  isolated copy (project requirement: >=80%).
- `[PASS]` 41/41 tests pass in the working tree and again, independently, in
  an isolated scratch copy of the code.
- `[NOT RUN]` Real Ollama endpoint / GUI interaction -- not applicable
  (`requests.post` is mocked in all `OllamaProvider` tests per the project's
  "no real network calls" testing rule; ticket has no GUI/CLI requirement).

**Honesty note on independence**: this verification was performed by the same
Claude session that wrote the implementation, not by a separate reviewer or
model (same caveat flagged in TASK-002's verification record). It does follow
the isolated-copy-and-independently-rerun discipline the project asks for,
plus a manual by-eye file inspection beyond just re-running pytest, but it is
not the same strength of evidence as an independent second reviewer.
