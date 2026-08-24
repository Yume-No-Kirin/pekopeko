# TASK-001: Data Ingestion Module (V1)

- **Status**: completed

## Objective

Implement a minimal ingestion pipeline: given a single Markdown (`.md`) source file, preserve the source, extract atomic knowledge assertions via a pluggable LLM provider, and write them as review-pending Proposal items. Implements `SOURCE → AI INTERPRETATION/EXTRACTION → PROPOSAL` from `specs/domain/knowledge-model.md`. Stops at PROPOSAL — human review (accept/reject into canonical) is a separate future ticket.

This ticket is self-contained: independent of any other ticket or existing code, including `knowledge_core/storage.py`. It implements its own minimal file-writing logic rather than importing another module (explicit product decision). It must still conform to the `Accepted` ADRs below, regardless of which code implements them.

## Binding context (references, not duplicated here)

- `specs/domain/knowledge-model.md` — conceptual flow and definitions of Source, Assertion, Proposal.
- ADI-001 (canonical-persistence-model, Accepted): one structured file per item (YAML frontmatter + body), domain-scoped directories, stable explicit IDs, no database, no git, atomic writes required.
- ADI-004 (obsidian-role, Accepted): vault layout `<domain>/<item-type-plural>/<item-id>/<item-id>.md`, with folders `entities/assertions/events/relationships/proposals`. **This ticket adds a sixth per-domain folder, `sources/`**, for preserved raw source material — required by CAP-002 and UC-001, not covered when ADI-004 was written. Treated as a minor consistent extension, not a contradiction.
- ADI-005 (sync-vs-async, Accepted), Rule 1: ingestion/extraction is async, runs as a background task; result is a Proposal added to the review queue; user never blocked. In-flight task state must be persisted locally, outside the vault, per-device, recoverable.
- ADI-007 (implementation-language, Accepted): Python.
- ADI-008 (llm-provider-architecture, Accepted): extraction must go through a pluggable provider interface (`extract(text, context) -> ExtractionResult`); pipeline code must never import/reference a provider SDK directly; active provider chosen by local config. No default provider mandated (a local Ollama endpoint is suggested as simplest).
- `specs/domain/knowledge-invariants.md`:
  - INV-001: ingestion must never write directly to canonical status — only Proposal items.
  - INV-002 / INV-016: extracted assertions must carry `epistemic_status` distinguishing them from directly-sourced fact, plus provenance to the exact source.
  - INV-003: every Proposal traceable to its source and the processing step that produced it.
  - INV-007: distinguish when a source was ingested from when its content claims to be true/applicable.
  - INV-019: a failed extraction must not corrupt the source or leave a partially-written Proposal file — must leave inspectable, honest failure state.
  - INV-020: re-ingesting the same source content must not blindly create duplicate proposals.
- `specs/product/capabilities.md`, CAP-002: store source materials separately from extracted knowledge; all canonical knowledge human-reviewed; AI-generated info cannot auto-become canonical.
- `specs/product/use-cases.md`, UC-001 (Novel Ingestion), UC-007 (Multimodal Ingestion), UC-016 (Duplicate/Repeated Ingestion) — framing use cases.

## Scope

Implement a Python package providing an ingestion pipeline that:

1. Reads a single Markdown source file from a given path.
2. Preserves that source as a canonical-compatible file under the vault.
3. Detects exact-duplicate re-ingestion (by content hash) and skips reprocessing if already ingested.
4. Calls a pluggable LLM provider to extract a list of atomic assertions from the source text.
5. Writes each extracted assertion as a Proposal file with `proposal_status: PROPOSED`.
6. Tracks the state of each ingestion attempt (pending/running/completed/failed) in local, non-canonical storage outside the vault.

### V1 scope decisions

- **Assertion extraction only.** Entity, Event, Relationship extraction are separate, out-of-scope problems.
- **Only `.md` sources in V1**, but reading is behind an extensible reader registry keyed by file extension — adding a new format later means adding a reader, not modifying the pipeline.
- **`domain` is passed explicitly to the pipeline**, never inferred (INV-008/AP-005).
- **Exactly one concrete LLM provider required** (a local Ollama HTTP endpoint recommended), reached only through the `extract()` interface — never called directly from pipeline code.
- **Duplicate detection is exact-content-hash only.** Detecting a *modified* re-ingestion of a previously-seen source is out of scope.
- **Task state is minimal**: one local record per attempt with a status field — not a general-purpose task queue/orchestrator.

### File layout (exact contract)

```
<vault_root>/<domain>/sources/<source_id>/<source_id>.md
<vault_root>/<domain>/proposals/<proposal_id>/<proposal_id>.md
```

- `domain` ∈ {PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING} (AP-005/INV-008), passed explicitly by the caller.
- `source_id` derived deterministically from content: `src-<sha256(content)[:16]>`. Duplicate detection = "does a source file with this ID already exist" — no separate duplicate index needed.
- `proposal_id` fresh per assertion: `prop-<uuid4>`.
- No history subfolder: sources and proposals are create-only in this scope. Re-ingesting an existing `source_id` → detect duplicate, skip (Acceptance Criterion 3) — never update/overwrite.
- Each `.md` file: YAML frontmatter (`---`-delimited) + markdown body.

### Required frontmatter — Source file

- `id` (string, matches `source_id`)
- `type`: `source`
- `domain` (string, one of the five domains)
- `source_format` (string, e.g. `markdown`)
- `original_filename` (string)
- `content_hash` (string, sha256 hex digest of raw content)
- `ingested_at` (ISO 8601 timestamp)
- `lifecycle_status`: `ACTIVE`

Body: the original file content, byte-for-byte preserved (trivial for `.md`, already plain text).

### Required frontmatter — Proposal file

- `id` (string, matches `proposal_id`)
- `type`: `proposal`
- `domain` (string, same domain as the source)
- `proposal_status`: `PROPOSED` (the only value this ticket writes; full lifecycle `PROPOSED → EDITED → ACCEPTED → CANONICAL` / `PROPOSED → REJECTED` per KSR-007/KSR-013 is future work)
- `proposed_item_type`: `assertion` (fixed in this ticket's scope)
- `epistemic_status` (string, one of `direct`/`inferred`/`uncertain`/`contested` — default `inferred` unless the provider signals otherwise; never omit)
- `created_at` (ISO 8601 timestamp — when the proposal was generated)
- `valid_from` / `valid_until` (ISO 8601 timestamp or null — claimed validity of the content, distinct from `created_at`, per INV-007)
- `provenance` (dict): minimum `source_id` (pointer to the Source file) and `extraction_provider` (name/identifier of the producing provider)

Body: the extracted assertion's full text — a full embedded snapshot (not a reference-only diff), consistent with ADI-001.

### Provider interface (per ADI-008)

```python
@dataclass
class ExtractedAssertion:
    text: str
    epistemic_status: str  # "direct" | "inferred" | "uncertain" | "contested"

@dataclass
class ExtractionResult:
    assertions: list[ExtractedAssertion]

class Provider(Protocol):
    def extract(self, text: str, context: dict) -> ExtractionResult: ...
```

Pipeline code may only depend on this interface. Exactly one concrete implementation required for V1 (e.g. `OllamaProvider`), in its own module — the only place allowed to make the actual HTTP/SDK call to the LLM. Provider selection (which concrete class to instantiate) happens via local configuration (config file or env var), never a hardcoded import in the pipeline.

### Reader interface (source-format extensibility)

```python
class SourceReader(Protocol):
    def read(self, path: Path) -> str: ...  # returns raw text content
```

A registry maps file extension (or MIME type) to a `SourceReader` implementation. V1 requires exactly one registered reader, for `.md`. Adding a second file type later must only require registering a new reader, not modifying pipeline orchestration logic (Acceptance Criterion 5).

### Task state

One record per ingestion attempt, persisted as a local file (JSON or equivalent) outside the vault (per ADI-005 placement rule — local, per-device, not synced, not canonical). Minimum fields: `task_id`, `source_path`, `domain`, `status` (`pending`/`running`/`completed`/`failed`/`skipped_duplicate`), `started_at`, `completed_at` (nullable), `error` (nullable), `source_id` (nullable until resolved), `proposal_ids` (list, empty until populated). Loss of this state must never corrupt or affect canonical/proposal data — the safe fallback is simply resubmitting the ingestion attempt.

## Requirements

- Python only (ADI-007). `pyyaml` for frontmatter; an HTTP client (`requests` or stdlib) for the Ollama provider — no other new dependency without a stated reason.
- All directory creation (domain folder, `sources/`/`proposals/` folders, per-item folder) happens automatically as needed.
- Missing or invalid required frontmatter fields raise a clear, typed validation error before any file is written.
- No use of git anywhere in the implementation (ADI-001).
- Must not depend on Obsidian being installed or running.
- All writes to `sources/` and `proposals/` files are atomic (write to a temp file in the same directory, then `os.replace()` or equivalent).

## Constraints

- No Entity/Event/Relationship extraction — Assertion only.
- No proposal accept/reject/edit workflow — this ticket stops at writing `proposal_status: PROPOSED` files.
- No database of any kind (SQLite or otherwise) — task state and duplicate detection are plain files.
- No GUI or CLI required (a Python function entry point is sufficient).
- No semantic/fuzzy duplicate detection — exact content-hash match only.
- No dependency on `knowledge_core/` or any other existing module in this repository — implement independent atomic file-writing logic, even though the output follows the same ADI-001/ADI-004 frontmatter contract. (Known short-term duplication with `knowledge_core/storage.py` accepted; consolidation is future work.)

## Files/modules concerned

Suggested layout (adjust if a clearer structure emerges, but keep module boundaries matching the interfaces above):

- `ingestion/providers/base.py` — `ExtractedAssertion`, `ExtractionResult`, `Provider` protocol.
- `ingestion/providers/ollama_provider.py` — concrete `OllamaProvider`.
- `ingestion/readers/base.py` — `SourceReader` protocol and the registry.
- `ingestion/readers/markdown_reader.py` — concrete markdown reader.
- `ingestion/storage.py` — atomic write helpers for Source and Proposal files, frontmatter validation.
- `ingestion/task_state.py` — task state record read/write.
- `ingestion/pipeline.py` — orchestration: `ingest_source(vault_root, domain, source_path, provider) -> IngestionResult`.
- `tests/ingestion/` — mirroring the modules above.

## Dependencies

None. Independent of any other ticket or existing module in this repository.

## Acceptance criteria

1. Ingesting a `.md` source file produces a Source file at `<domain>/sources/<source_id>/<source_id>.md` with all required frontmatter fields, and one Proposal file per extracted assertion at `<domain>/proposals/<proposal_id>/<proposal_id>.md` with all required frontmatter fields, including `proposal_status: PROPOSED` and `provenance.source_id` pointing at the Source file just created.
2. No pipeline code (`ingestion/pipeline.py`, `ingestion/storage.py`, `ingestion/readers/*`) imports or references a concrete LLM SDK/HTTP client directly — only `ingestion/providers/ollama_provider.py` (or equivalent) does. Verifiable by static inspection.
3. Ingesting the exact same source file a second time (same content, same domain) creates no new Source file or Proposal files — the pipeline detects the existing `source_id` and returns a result indicating a skipped duplicate (INV-020).
4. If the provider's `extract()` call raises/fails (simulated in a test): no partial or corrupt Source or Proposal file is left on disk, the original input file is untouched, and the task state record reflects `status: failed` with a non-null `error`.
5. Adding a second registered reader (e.g. a trivial `.txt` reader used only in a test) requires no changes to `ingestion/pipeline.py` — only a new reader module plus a registry entry.
6. Swapping the configured provider for a second, minimal test/fake provider (implementing the same `Provider` protocol) requires no changes to `ingestion/pipeline.py` — only local configuration.
7. Every extracted assertion's Proposal frontmatter includes an `epistemic_status` value from `{direct, inferred, uncertain, contested}` — never omitted, never silently defaulted to something implying certainty.
8. All Source/Proposal writes are atomic: verified either by inspecting for temp-file-then-rename behavior in code, or by simulating a failure mid-write and confirming no partial file is left behind.
9. `grep -r "git"` over the `ingestion/` implementation shows no use of git tooling/libraries for historization.

## Testing requirements

`pytest` unit tests covering every acceptance criterion above. Use `tmp_path` (or equivalent) as `vault_root` and a local temp directory for task state — tests must never touch a real Obsidian vault or write anything outside their own temp directories. The LLM provider must be mocked/faked in tests (no real network calls) except, optionally, one clearly-marked integration test skipped by default. Include at least:
- A first-ingestion test asserting the full file layout and frontmatter contract (Criterion 1).
- A static-inspection or import-graph test for provider isolation (Criterion 2).
- A duplicate-ingestion test (Criterion 3).
- A simulated provider-failure test (Criterion 4).
- A second-reader extensibility test (Criterion 5).
- A second-provider extensibility test (Criterion 6).

## Out of scope

- Entity, Event, and Relationship extraction — future ticket(s).
- Proposal review/accept/reject/edit workflow (AP-002) — future ticket, produces canonical knowledge from these proposals.
- Any file format other than `.md` (PDF, audio, video, images, web pages — UC-007) — future ticket(s), enabled by the reader registry this ticket establishes.
- Semantic/near-duplicate detection, staleness detection on source modification (UC-003, richer parts of UC-016).
- A real asynchronous task orchestrator/queue — this ticket only defines the task-state record shape, not a scheduler.
- Any GUI or CLI.
- A second or third concrete LLM provider beyond the one required for V1.
- Consolidating this module's storage logic with `knowledge_core/storage.py` or any other existing module.
