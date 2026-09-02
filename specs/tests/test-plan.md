# Pekopeko Test Plan (Cahier de Tests)

Human- and AI-readable test book, traced to `specs/product/use-cases.md` (UC-001..UC-018)
and to the tickets actually implemented (`specs/tasks/completed/`). Built strictly from
those sources plus direct, verified observation of the running code — nothing here is an
invented or assumed behavior.

## Scope and update discipline

This document is **exhaustive over all 18 use cases**, but **automated only where the
code actually supports it today**. Pekopeko's product vision (`specs/product/use-cases.md`)
describes domain modules (Fiction, Personal Planning, Japanese Learning, Research),
retrieval, reasoning, and knowledge-health monitoring that do not exist in code yet — only
eight tickets are `completed` as of this writing: TASK-001, TASK-001a, TASK-001b,
TASK-002, TASK-003, TASK-004, TASK-006, TASK-007 (generic ingestion of Assertions,
Entity/Event/Relationship extraction, Proposal review/accept/reject/edit for assertions,
local config, and an HTTP API wrapper — no domain module, no retrieval, no reasoning, no
GUI).

Each UC section below is marked:
- ✅ **Covered** — the UC's goal is fully implemented and tested.
- 🟡 **Partial** — only a slice of the UC is implemented; the slice is tested, the rest is
  named as a gap, not silently dropped.
- ⛔ **Not testable** — the capability the UC needs doesn't exist in code yet; no test
  case is listed, only the one-line reason.

**Maintenance rule**: when a `backlog` ticket (TASK-005, TASK-007a, TASK-008..TASK-012, …)
lands, update that UC's section — status, test cases, automation pointers — as part of
the same session, the same way `docs/ROADMAP.md`'s "État actuel" gets updated. This is
what keeps the cahier usable throughout the rest of development instead of going stale.

## Test layers

Two independent, complementary layers exist under `src/tests/`:

1. **`src/tests/acceptance/`** — deterministic, direct calls to the real pipeline
   functions (`ingest_source`, `extract_source`, `review.*`, `load_config`), with a
   hand-rolled fixed-output fake provider standing in only for the LLM call. No network,
   no Flask. Every `TC-UC0XX-NN` case below has an entry here with exact expected
   values — **this is the precise, reproducible backbone of the cahier**, and it is what
   satisfies "results must not differ from one run to another." Runs everywhere, always,
   as part of a plain `pytest` invocation.
2. **`src/tests/e2e/`** — real end-to-end: a genuine Flask server (`create_app()`, served
   via `werkzeug.serving.make_server` on a real socket, not `test_client()`), driven with
   real HTTP requests (`requests`) against a real local Ollama. Only flagship flows are
   covered here (not every AC), and only structure/contract is asserted (status codes,
   required fields present, valid enum membership, file existence, counts) — never exact
   LLM wording, since that varies between runs. Marked `@pytest.mark.e2e`, **excluded by
   default** (`pytest.ini`'s `addopts = -m "not e2e"`); run explicitly with
   `pytest -m e2e` when a local Ollama is running. A session-scoped `ollama_reachable`
   fixture skips the whole layer with a clear reason if Ollama isn't reachable, so other
   environments (e.g. one only running the externalized qwen3-coder Ollama per
   `AGENTS.md`) still get a clean run of everything else. **The configured model must
   also be pulled locally** (default `llama3`, override via `PEKOPEKO_OLLAMA_MODEL`) —
   if it isn't, the reachability check still passes (Ollama itself responds) but the
   ingestion/extraction task will reach `status: "failed"` with a provider error, which
   the E2E tests will report as a real failure, not a skip. This layer was verified in
   this session against a real local Ollama (`qwen2.5:7b`) — all 7 e2e tests pass; see
   "Findings surfaced while building this suite" below for two real gaps it caught.

Neither layer duplicates TASK-007's own HTTP contract tests (auth, CORS, error-mapping
table, bind host) — those already live in `src/tests/api/` and are out of scope here.

### How to run

```
pytest src/tests/acceptance/ -v          # deterministic layer, always safe, no Ollama needed
pytest src/tests/ -m "not e2e" -q        # everything except the real-server layer (default)
pytest src/tests/e2e/ -m e2e -v          # real server + real Ollama, opt-in
```

### Known pre-existing issue (not introduced by this test suite, verified independently)

Running `pytest src/tests/` as one invocation across multiple module directories at once
(e.g. `config/` + `extraction/`) fails at **collection**, not at test time, with
`ImportError: cannot import name 'X' from '_helpers'` pointing at the wrong directory's
`_helpers.py`. Cause: `src/tests/{config,extraction,api}/` each define their own
`_helpers.py`, and no directory under `src/tests/` has an `__init__.py`, so pytest's
rootless import mode registers each as the same flat module name `_helpers` in
`sys.modules` — whichever is imported first wins, and a later, differently-shaped
`_helpers.py` in another directory then fails to resolve its own names. **Confirmed via
`git stash` that this predates this test-plan session** — it is not something introduced
here. This test plan's own new helper modules are deliberately named
`_acceptance_helpers.py` and `_e2e_helpers.py` (not `_helpers.py`) specifically so they
don't add a fourth/fifth collision to this pre-existing one. Workaround until fixed: run
each module directory separately (as the counts in `docs/ROADMAP.md` already imply were
being run), or add `__init__.py` files under `src/tests/*/` (out of this task's scope —
flagged for Cleo, not silently fixed).

## Findings surfaced while building this suite

These were discovered by writing and running real tests against real code (including a
real server and real Ollama) — not assumed, not read off a comment. Both concern the same
root cause and are re-flagged in their UC sections below; collected here for visibility
since they matter beyond a single UC.

1. **Entity/Event/Relationship proposals are invisible to the entire `review/` layer,
   not just unsupported for accept.** `extraction/storage.py` (TASK-003's own,
   deliberately independent contract) writes proposal frontmatter with `item_type` and no
   top-level `id` field. `review/storage.py`'s `REQUIRED_PROPOSAL_FIELDS` (TASK-002)
   requires `id`/`type`. Consequences, verified against a real server:
   - `GET /domains/<domain>/proposals` (`review.list_proposals`) **silently omits every
     extraction-produced proposal** — no error, just missing from the list — because
     `list_proposals` catches `ValidationError` per-item and `continue`s past malformed
     entries. A real extraction that completes with 6 proposals on disk shows up as `[]`
     through this endpoint.
   - `GET /domains/<domain>/proposals/<id>` and `POST .../accept` on one of those IDs
     both return **HTTP 400** (`error.type: "ValidationError"`, "Missing required
     frontmatter fields: ['id', 'type']") — the request never reaches the
     `proposed_item_type` check at all.
   - This means TASK-009/TASK-010/TASK-011's future GUI review screens, built against
     today's API, would show **zero** entity/event/relationship proposals in the queue —
     not "present but not actionable," genuinely absent — even once TASK-005 adds
     accept/reject support for them, unless TASK-005 also reconciles the two contracts'
     field names (or `review/` is taught to read both).
2. **TASK-007's own AC10 ("`POST .../accept` on an entity/event/relationship proposal
   returns `422`") is not reachable with a real extraction-produced proposal — it returns
   `400` instead.** The existing regression test for AC10
   (`src/tests/api/test_review_routes.py::test_accept_entity_proposal_returns_422`) uses
   `api/conftest.py`'s `make_proposal_file` fixture, which constructs its proposal using
   the **ingestion/review** contract's field names (`id`/`type` present) with
   `proposed_item_type="entity"` — a shape that never actually arises from
   `extract_source()`'s real output. So that test is testing a hypothetical proposal
   shape, not the real one; both can be true (`422` for the hypothetical shape, `400` for
   the real one) without either test being wrong, but AC10 as *described* in
   `specs/tasks/completed/TASK-007-backend-api-layer.md` doesn't hold for genuine
   extraction output.

Both are re-tested as explicit regression guards in `src/tests/acceptance/
test_ingestion_to_review_end_to_end.py` (deterministic) and `src/tests/e2e/
test_extraction_e2e.py` (real server + real Ollama) — see UC-001 and UC-011 below.

---

## UC-001 — Novel Ingestion

🟡 **Partial.** Goal: process a manuscript and extract knowledge for review. The generic
Core mechanics (source preservation, extraction, proposal generation, review-queue entry)
are implemented; the FICTION-domain-specific interpretation is not (there is no Fiction
module — `domain` is just a folder-partition label).

#### TC-UC001-01 — Assertion full round trip: source → proposal → accept → canonical
- **Validates:** UC-001 stages 1,3,7,8,9,10 (assertions only) · TASK-001 AC1,AC7 ·
  TASK-002 AC1 · INV-001, INV-002, INV-003, INV-018, INV-020
- **Preconditions:** empty `tmp_path` vault; fixed fake provider returns one assertion
  (`epistemic_status="direct"`)
- **Steps:** 1) `ingest_source(...)` 2) assert Source+Proposal files and required fields
  3) `accept_proposal(...)` 4) assert canonical Assertion file, provenance chain
  (`proposal_id`, `source_id`, `reviewed_by`), proposal now `ACCEPTED` with
  `resulting_item_id`
- **Expected result:** every field asserted exactly (fixed provider ⇒ fixed content)
- **Automation (deterministic):**
  `src/tests/acceptance/test_ingestion_to_review_end_to_end.py::test_assertion_full_round_trip_creates_traceable_canonical_item`
- **Automation (real E2E, best-effort):**
  `src/tests/e2e/test_ingestion_e2e.py::test_ingestion_round_trip_via_real_server_and_ollama`
  — structural only (status codes, `epistemic_status` ∈ valid set, file existence; not
  exact assertion text)
- **Determinism notes:** deterministic layer uses a fixed provider, exact-value
  assertions, no network. E2E layer's outcome (pass/fail) is stable; its *content* is not
  — see "Test layers" above.

#### TC-UC001-02 — Entity/Event/Relationship: proposals created, accept fails (documented gap)
- **Validates:** UC-001 stages 1,3,7,8 (entity/event/relationship) · TASK-003 AC1,AC7 ·
  **Finding 1/2 above** (regression guard, not a feature test)
- **Preconditions:** same as above, extraction pipeline, fixed fake provider returns 2
  entities + 1 event + 1 relationship
- **Steps:** 1) `extract_source(...)` 2) assert 4 Proposal files, all `PROPOSED`, correct
  `proposed_item_type` set 3) `accept_proposal(...)` on each → assert
  `review.errors.ValidationError` (not `UnsupportedProposalTypeError` — see Finding 2)
  4) assert proposal file unchanged (still `PROPOSED`) after the failed attempt
- **Expected result:** proposals created correctly; accept fails loudly with
  `ValidationError`, no partial state
- **Automation (deterministic):**
  `src/tests/acceptance/test_ingestion_to_review_end_to_end.py::test_entity_event_relationship_extraction_stops_at_proposed_and_accept_is_unsupported`
- **Automation (real E2E, best-effort):**
  `src/tests/e2e/test_extraction_e2e.py::test_extraction_completes_and_creates_proposals_on_disk`,
  `::test_extraction_proposals_are_invisible_to_the_review_queue_endpoint`,
  `::test_extraction_proposal_get_and_accept_fail_with_validation_error`
- **Determinism notes:** the `ValidationError`/400/list-emptiness assertions are
  content-independent (they hold regardless of what the LLM actually extracted, as long
  as it extracts ≥1 item) — fully deterministic even in the real-E2E layer.
- **Gap named, not silently cut:** review/accept for these types is TASK-005 (`backlog`);
  the deeper contract mismatch (Finding 1/2) means TASK-005 must reconcile field names
  too, not just add business logic.

Not covered: FICTION-domain-specific interpretation (no Fiction module exists);
multimodal source formats (see UC-007).

---

## UC-002 — Complete Character Profile

⛔ **Not testable.** Needs knowledge retrieval and reasoning over relationships
(CAP-CORE-010/011) — no code implements either.

---

## UC-003 — Novel Change and Staleness

🟡 **Partial (thin).** Real current behavior: a modified source produces an entirely
independent new Source (different content hash) with no linkage or staleness marking to
the old one. True staleness propagation (CAP-CORE-006, derived-knowledge dependency
tracking) is not implemented.

#### TC-UC003-01 — Modified source is independent, no linkage
- **Validates:** UC-003 stage 1 (change detection, negative result) · INV-004 (old Source
  untouched)
- **Preconditions:** ingest v1 of a source, then overwrite the same path with different
  content
- **Steps:** 1) ingest v1 2) overwrite file content 3) ingest v2 4) assert `source_id`
  differs, v1's Source file untouched (content unchanged), v2's Source file doesn't
  reference v1's `source_id` anywhere
- **Expected result:** two fully independent Sources, no cross-reference
- **Automation (deterministic):**
  `src/tests/acceptance/test_duplicate_and_modified_ingestion.py::test_modified_source_produces_independent_new_source_no_linkage`
- **Determinism notes:** fixed provider, exact hash comparison, no network.

Not covered: staleness marking of derived knowledge, diffing between versions, any
notion that v2 "replaces" v1.

---

## UC-004 — Personal Event and Schedule Conflict

⛔ **Not testable.** Conflict-detection reasoning is not implemented. Generic event
proposal creation is already exercised by TC-UC001-02 via the extraction pipeline — no
separate test needed for that slice.

---

## UC-005 — "Why Did I Make This Decision?"

⛔ **Not testable.** Explanation/reasoning generation over historical knowledge is not
implemented.

---

## UC-006 — Japanese Learning

⛔ **Not testable.** No Japanese Learning module exists.

---

## UC-007 — Multimodal Ingestion

🟡 **Partial (pointer only, no new test).** Only a `.md` reader exists
(`readers/markdown_reader.py` in both `ingestion/` and `extraction/`). The extensibility
guarantee — a new reader can be registered without changing pipeline code — is TASK-001
AC5 / TASK-003 AC5, already tested by the existing per-ticket suite. Duplicating that
here would add nothing; the cahier cites it instead:
- `src/tests/ingestion/test_extensibility.py`
- `src/tests/extraction/test_extensibility.py`

Not covered: PDF, image, audio, video, web page, or any other format — no reader exists
for any of them.

---

## UC-008 — Research

⛔ **Not testable.** Synthesis/comparison reasoning across sources is not implemented.
Its only implemented ingredient (generic source ingestion) is already covered by
TC-UC001-01.

---

## UC-009 — Cross-Domain Analysis

🟡 **Partial.** Only domain-level isolation (INV-008 — no operation crosses a domain
boundary implicitly) is implemented and testable. Explicit authorized cross-domain
analysis (CAP-CORE-014) does not exist.

#### TC-UC009-01 — `list_proposals` never leaks across domains
- **Validates:** INV-008
- **Steps:** ingest into PERSONAL and FICTION separately; `list_proposals` for each
  domain returns only that domain's own proposal IDs
- **Automation (deterministic):**
  `src/tests/acceptance/test_domain_isolation.py::test_list_proposals_never_leaks_across_domains`

#### TC-UC009-02a — Cross-domain proposal lookup by path is a plain not-found
- **Validates:** INV-008
- **Steps:** ingest under FICTION; `get_proposal(vault_root, "PERSONAL", <that id>)` →
  `ProposalNotFoundError` (different domain = different folder tree entirely)
- **Automation (deterministic):**
  `src/tests/acceptance/test_domain_isolation.py::test_get_proposal_under_wrong_domain_path_is_not_found`

#### TC-UC009-02b — Frontmatter/folder domain mismatch is rejected explicitly
- **Validates:** INV-008 (defense against a corrupted/hand-edited file, not just the
  happy path)
- **Steps:** hand-write a proposal file under `PERSONAL/proposals/...` whose frontmatter
  `domain` field says `FICTION`; `get_proposal(vault_root, "PERSONAL", id)` →
  `DomainMismatchError`
- **Automation (deterministic):**
  `src/tests/acceptance/test_domain_isolation.py::test_get_proposal_with_mismatched_frontmatter_domain_is_rejected`

#### TC-UC009-E2E-01/02 — Real cross-domain 404s
- **Automation (real E2E, best-effort):**
  `src/tests/e2e/test_domain_isolation_e2e.py::test_ingestion_task_is_not_found_under_a_different_domain`,
  `::test_proposal_is_not_found_under_a_different_domain`
- **Determinism notes:** routing/isolation assertions, content-independent — fully
  deterministic even with a real LLM.

Not covered: any authorized cross-domain operation (none exists to test), compatibility
analysis between domains.

---

## UC-010 — Correction Propagation

⛔ **Not testable.** No canonical-item correction or impact-analysis mechanism exists —
TASK-006's `edit_proposal` only edits pre-acceptance Proposals, never an already-accepted
canonical item.

---

## UC-011 — Review Queue

🟡 **Partial (best-covered UC in the repo).** The V1 individual-review slice is fully
implemented: list (status filter), get (+ resolved source), accept, reject (+ reason),
edit (+ history versioning), invalid-transition guard. Bulk operations, richer
filtering/sorting/grouping, and analytics are not implemented. **Finding 1 above** also
belongs here: the review queue is silently blind to every entity/event/relationship
proposal.

#### TC-UC011-01 — `list_proposals` filters by status
- **Validates:** TASK-002 AC6
- **Automation (deterministic):**
  `src/tests/acceptance/test_review_queue_workflow.py::test_list_proposals_filters_by_status`

#### TC-UC011-02 — Edit then accept reflects edited content, with history versioning
- **Validates:** TASK-006 AC1,AC8 · INV-004, INV-018
- **Steps:** edit a `PROPOSED` proposal's body → assert `history/` snapshot (`v1`,
  `SUPERSEDED`, `superseded_by: v2`) with the exact pre-edit content, live file now
  `EDITED` with new content → accept → canonical body matches the *edited* text
- **Automation (deterministic):**
  `src/tests/acceptance/test_review_queue_workflow.py::test_edit_proposal_then_accept_reflects_edited_content_with_history`

#### TC-UC011-03 — Reject with reason preserves content
- **Validates:** TASK-002 AC2 · INV-005
- **Automation (deterministic):**
  `src/tests/acceptance/test_review_queue_workflow.py::test_reject_with_reason_preserves_content_and_sets_reason`

#### TC-UC011-04 — Accept on non-`PROPOSED` status raises, no duplicate canonical item
- **Validates:** TASK-002 AC4 (regression coverage)
- **Automation (deterministic):**
  `src/tests/acceptance/test_review_queue_workflow.py::test_accept_on_non_proposed_status_raises_and_leaves_files_untouched`

#### TC-UC011-E2E-01/02 — Finding 1/2, real server (see "Findings" section above)
- **Automation (real E2E, best-effort):**
  `src/tests/e2e/test_extraction_e2e.py::test_extraction_proposals_are_invisible_to_the_review_queue_endpoint`,
  `::test_extraction_proposal_get_and_accept_fail_with_validation_error`
- **Determinism notes:** content-independent (list-emptiness and error-type assertions
  hold regardless of what the LLM extracted).

Not covered: bulk accept/reject, filtering beyond `status`, sorting, grouping,
prioritization, review analytics.

---

## UC-012 — Knowledge Health

⛔ **Not testable.** Capability not even formally specified yet — `docs/ROADMAP.md`'s own
open point #3 notes "Knowledge Health / Integrity Monitoring" is referenced in
`use-cases.md` with no corresponding formal capability in `specs/architecture/capabilities.md`.

---

## UC-013 — Recurring Needs

⛔ **Not testable.** No recurring-requirement concept exists in code.

---

## UC-014 — Source-Based Question Answering

🟡 **Partial (folded into UC-011's coverage, no separate test file).** `get_proposal`
resolves and returns the linked Source's content — the testable provenance/retrieval
slice behind this UC's goal. Real answer generation is not implemented.

#### TC-UC014-01 — `get_proposal` resolves linked source content exactly
- **Validates:** TASK-002 AC7 · INV-003, INV-016
- **Steps:** ingest a source with known exact content → `get_proposal(...).source_body`
  equals the original content byte-for-byte
- **Automation (deterministic):**
  `src/tests/acceptance/test_review_queue_workflow.py::test_get_proposal_resolves_linked_source_content_exactly`

Not covered: answering a natural-language question about the source, any reasoning over
source content.

---

## UC-015 — Knowledge Change History

⛔ **Not testable** for its actual goal (querying a *canonical* item's state as of a past
point in time). TASK-006's `history/` mechanism is Proposal-level only, and applies only
before acceptance — not counted as coverage of this UC, to avoid overstating what exists.
Canonical (accepted) items have no history/versioning mechanism at all in the 8 completed
tickets.

---

## UC-016 — Duplicate / Repeated Ingestion

✅ **Covered.** INV-020 is directly implemented and required (TASK-001 AC3, TASK-003
AC3) for both pipelines.

#### TC-UC016-01 — Duplicate ingestion: no new files, provider called once
- **Validates:** TASK-001 AC3 · INV-020
- **Automation (deterministic):**
  `src/tests/acceptance/test_duplicate_and_modified_ingestion.py::test_duplicate_ingestion_creates_no_new_files_and_skips_provider_call`

#### TC-UC016-02 — Duplicate extraction: same guarantee, independent pipeline
- **Validates:** TASK-003 AC3 · INV-020
- **Automation (deterministic):**
  `src/tests/acceptance/test_duplicate_and_modified_ingestion.py::test_duplicate_extraction_creates_no_new_files_and_skips_provider_call`

#### TC-UC016-E2E-01 — Real duplicate ingestion reaches `skipped_duplicate`
- **Automation (real E2E, best-effort):**
  `src/tests/e2e/test_duplicate_ingestion_e2e.py::test_duplicate_ingestion_via_real_server_reaches_skipped_duplicate`
- **Determinism notes:** exact-value deterministic even with a real LLM — dedup
  short-circuits *before* the provider is ever called, so the outcome never depends on
  LLM content.

---

## UC-017 — Uncertainty

🟡 **Partial.** `epistemic_status` (direct|inferred|uncertain|contested) is required on
every proposal, never silently defaulted, and carried through unchanged to the canonical
Assertion on accept. Numeric confidence scores and contradiction-linking are not
implemented.

#### TC-UC017-01 — `epistemic_status` preserved through ingestion and acceptance
- **Validates:** TASK-001 AC7 · INV-002, INV-014
- **Automation (deterministic):**
  `src/tests/acceptance/test_uncertainty_preservation.py::test_epistemic_status_preserved_through_ingestion_and_acceptance`

#### TC-UC017-02 — All 4 vocabulary values round-trip unchanged (extraction)
- **Validates:** TASK-003 AC7 · INV-014
- **Automation (deterministic):**
  `src/tests/acceptance/test_uncertainty_preservation.py::test_all_four_epistemic_statuses_accepted_for_extraction_proposals`
  (parametrized: direct, inferred, uncertain, contested)

#### TC-UC017-03a/b — Invalid `epistemic_status` rejected before any write (both pipelines)
- **Validates:** TASK-001 AC7, TASK-003 AC7 · INV-014, INV-019 (never silently coerced
  to an implied-certainty default)
- **Automation (deterministic):**
  `src/tests/acceptance/test_uncertainty_preservation.py::test_invalid_epistemic_status_rejected_before_any_ingestion_write`,
  `::test_invalid_epistemic_status_rejected_before_any_extraction_write`

Not covered: numeric confidence scores, contradiction detection/linking between
contested items.

---

## UC-018 — Fictional Universe Isolation

🟡 **Partial.** Only domain-level isolation is testable (shares TC-UC009-01/02's
guarantees). There is **no "context"/sub-domain concept** in the schema (e.g.
distinguishing two FICTION novels that happen to share a character name) — this UC's
actual goal is not covered.

#### TC-UC018-01 — Same-named entities across two extraction calls never merge
- **Validates:** demonstrates the system doesn't accidentally conflate same-named
  entities by construction (independent IDs) — does **not** demonstrate true
  universe/context isolation, which doesn't exist
- **Automation (deterministic):**
  `src/tests/acceptance/test_domain_isolation.py::test_same_name_entities_across_two_extraction_calls_never_merge`

Not covered: any notion of "universe" or "context" distinct from `domain` — no such field
exists anywhere in the frontmatter contract.

---

## Invariant traceability appendix (`specs/domain/knowledge-invariants.md`)

Reuses the `TC-UC0XX-NN` IDs already listed above — no test cases invented solely for
this table.

| Invariant | Status | Test case(s) / reason |
|---|---|---|
| INV-001 Universal Human Validation | Tested | TC-UC001-01, TC-UC011-04 |
| INV-002 AI Inference Is Not Sourced Fact | Tested | TC-UC017-01, TC-UC017-02 |
| INV-003 Provenance | Tested | TC-UC001-01, TC-UC014-01 |
| INV-004 History Is Never Silently Destroyed | Tested | TC-UC011-02, TC-UC003-01 |
| INV-005 Rejected ≠ False ≠ Unknown | Tested | TC-UC011-03 |
| INV-006 Contradictions Are Not Automatically Resolved | Not yet enforceable | no contradiction detection implemented |
| INV-007 Temporal Validity | Not directly tested | `valid_from`/`valid_until` fields exist and are carried through (TC-UC001-01, TC-UC011-02), but no temporal-reasoning behavior exists to test |
| INV-008 Domain Isolation | Tested | TC-UC009-01, TC-UC009-02a/b, TC-UC009-E2E-01/02 |
| INV-009 Explicit Cross-Domain Operations | Not yet enforceable | no cross-domain authorization mechanism implemented |
| INV-010 Modules Do Not Own the Core Knowledge Model | Architectural | not a runtime behavior this suite tests; see each module's own `test_import_isolation.py` |
| INV-011 Representations Are Not Canonical Truth | Architectural | no representation layer (GUI) exists yet |
| INV-012 Derived Knowledge Is Traceable | Not yet enforceable | no derived-knowledge computation implemented |
| INV-013 Derived Knowledge Can Become Stale | Not yet enforceable | same as INV-012 |
| INV-014 Uncertainty Remains Explicit | Tested | TC-UC017-01, TC-UC017-02, TC-UC017-03a/b |
| INV-015 Human Canonical Authority Is Not Objective Truth | Conceptual | not runtime-testable directly |
| INV-016 Source Content and Interpretation Remain Distinguishable | Tested | TC-UC014-01 |
| INV-017 Modules Remain Decoupled | Tested elsewhere | each module's own `test_import_isolation.py` (not duplicated here) |
| INV-018 Important Mutations Are Auditable | Tested | TC-UC001-01 (`reviewed_by`/`reviewed_at`), TC-UC011-02 (`edited_by`/`edited_at`) |
| INV-019 Failures Must Degrade Safely | Tested (mostly elsewhere) | TC-UC017-03a/b here; extensively covered by existing per-ticket write-failure atomicity tests (e.g. `review/test_pipeline_edit.py`) |
| INV-020 Repeated Ingestion Must Be Safe | Tested | TC-UC016-01, TC-UC016-02, TC-UC016-E2E-01 |
| INV-021 Knowledge Model Is Technology Independent | Architectural | not runtime-testable directly |
