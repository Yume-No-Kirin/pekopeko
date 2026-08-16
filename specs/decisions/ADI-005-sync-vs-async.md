# ADI-005: Synchronous vs. Asynchronous Operations

- **ID**: ADI-005
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`technical-requirements.md` (section 23) asks which operations should be synchronous vs asynchronous, citing CAP-CORE-012 (Asynchronous Task Management — TKR-001 Asynchronous Task Management, TKR-002 Task State Persistence) and all 18 use cases. Grounded directly in the use cases: ingestion (UC-001, UC-007) and correction propagation with impact analysis (UC-010) both involve AI/LLM processing that can take from seconds to minutes, while UC-011 (Review Queue) and most other use cases describe local reads (search, browsing, viewing history) that should feel immediate. UC-001's "Review Interruption" failure scenario ("System should maintain state and provenance even if review processes are interrupted") and TKR-002 both point to a real need for durable, recoverable task state — not just fire-and-forget background work.

## Decision

Three rules govern synchronous vs. asynchronous behavior:

1. **Anything requiring AI/LLM processing or non-trivial computation over the knowledge graph is asynchronous.** Ingestion/extraction (UC-001, UC-007), impact analysis for a correction (UC-010), and similar reasoning-heavy work run as background tasks. Their result is a Proposal added to the review queue (UC-011); the user is never blocked waiting on them.
2. **Anything that is a local read against already-persisted canonical files or derived indexes is synchronous.** Search (ADI-002's index), browsing a note, viewing history (ADI-001's per-item history subfolders) or relationships (ADI-003's adjacency structure), checking review queue state — these are fast local I/O with no external dependency, so there is no reason to make the user wait.
3. **Accepting or rejecting a proposal (human validation, AP-002) is synchronous from the user's perspective** — the resulting canonical file write (per ADI-001) applies immediately when the user acts. Any downstream consequence analysis this triggers (checking dependent/derived knowledge for staleness, per UC-010) is itself dispatched as a new asynchronous task, not computed inline before letting the user proceed.

**In-flight async task state** (what's running, its progress, enough to resume or report failure/recovery per TKR-002) is persisted locally, outside the Obsidian vault — the same placement reasoning as ADI-002's retrieval index, to avoid vault-sync conflicts — and per-device, not synced across devices (consistent with ADI-002/ADI-003). It is explicitly not canonical knowledge: per AP-002, nothing is canonical until human-reviewed, so if task state is ever lost, the safe fallback is that the task must be resubmitted — never that canonical knowledge becomes silently wrong or incomplete.

## Alternatives considered

- **Everything synchronous (block until AI/reasoning finishes).** Rejected: ingesting a novel manuscript (UC-001) or running impact analysis (UC-010) can take from seconds to minutes; blocking the user contradicts the product principle of a review-queue-based workflow where AI proposes asynchronously and the human reviews independently, not on demand while waiting.
- **Everything asynchronous, including local reads.** Rejected: reading already-persisted files or indexes is fast local I/O with no external dependency — forcing these through an async path would add latency and complexity for no benefit.
- **Task state stored as canonical files inside the vault.** Rejected: it is operational/process state, not knowledge about the world, and does not need the historization guarantees of AP-004 the way real knowledge items do. Treating it as vault-canonical would also reintroduce the sync-conflict risk already avoided for the retrieval index (ADI-002) and relationship structure (ADI-003).

## Consequences

- Any Phase 2/3 ticket involving ingestion, correction propagation, or other AI-driven analysis must design for asynchronous execution with resumable/recoverable task state from the start, not add it as an afterthought.
- The review queue (UC-011) is the natural surface where async task results land as proposals — its design should assume proposals can appear at any time, not only synchronously right after a user action.
- Cross-device behavior for in-flight tasks is intentionally simple for V1 (per-device, not synced). If genuine cross-device task visibility becomes a real need later, that should be a new ADR, not a silent addition.

## Phase 1 status

With this ADR accepted, all six Architectural Decision Inputs (ADI-001 through ADI-006) are `Accepted`. Phase 1 is complete — see `docs/ROADMAP.md` for the transition to Phase 2.
