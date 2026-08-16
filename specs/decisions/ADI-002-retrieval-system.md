# ADI-002: Semantic Retrieval System

- **ID**: ADI-002
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`technical-requirements.md` (section 23) frames this as "whether semantic retrieval should be integrated within primary database or use dedicated system," citing CAP-CORE-010 (Knowledge Search and Retrieval) and RTR-001..003 (search, ranking, performance). That framing assumed a primary database exists to potentially integrate retrieval into. ADI-001 (see `specs/decisions/ADI-001-canonical-persistence-model.md`) established that there is no primary database — canonical knowledge is stored as files — so the original either/or framing no longer applies as originally worded, and this ADR restates the decision in that context.

**Correction (2026-08-16, added after initial drafting):** `specs/product/use-cases.md` — not fully read when this ADR was first drafted — lists "Large-Scale Review: Managing hundreds of thousands of proposals efficiently" as an architectural pressure point. This materially weakens the "no index at all" fallback below; it is kept only as an explicit non-recommendation.

## Decision

Retrieval (full-text search now, semantic/embedding-based search later if needed) is implemented as a dedicated system, built as a **derived index** over the canonical files — never embedded inside canonical storage, since canonical storage is files, not a queryable database. It is explicitly not authoritative: it can be discarded and rebuilt at any time without any loss of canonical data.

Given the "hundreds of thousands of proposals" pressure point noted above, this index should be treated as required infrastructure for the review queue and search from early in V1, not as a "nice to have added later" — a naive linear scan of all files on every query is not expected to hold up at that volume.

**Where the index lives, and how it scales (decided 2026-08-16, at Cleo's request — "you know my end goals and constraints, propose what fits"):**

The index is never stored inside the Obsidian vault. The vault (per ADI-001) is synced continuously across devices by Cleo's own sync mechanism; an index cache file placed inside it would get swept into that sync as if it were a note, and a rebuild on one device could race against a synced copy from another. Instead, each device running Pekopeko builds and keeps its **own local index**, stored in a standard local application-data location outside the vault, rebuilt from the (synced) canonical files. This sidesteps sync conflicts entirely, the same way ADI-001 sidesteps them for git.

Concrete scaling path:
1. **V1, low volume:** no persisted index file at all — rebuilt in memory at startup by scanning the vault. Simplest possible option while item counts are small.
2. **Once startup scanning becomes noticeable:** persist the index as a local SQLite file using its full-text search extension (FTS5), stored outside the vault, updated incrementally as files change rather than fully rescanned each time. This is not a contradiction of ADI-001's rejection of SQLite — that rejection was specifically about SQLite as *canonical* storage; here it plays a completely different role, a disposable derived cache.
3. **If semantic search becomes necessary:** a local vector index is added alongside the FTS5 index — still local, still derived, still rebuildable, no server to run.
4. **Explicitly out of scope for now:** a shared, always-on index queryable simultaneously from multiple devices (a real search server). Nothing in the use cases describes concurrent multi-device querying — only single-device personal search. If that need materializes, it should be a new ADR, not a silent addition.

## Alternatives considered

- **Integrated within a primary database.** Moot given ADI-001; noted here only for traceability, since the original wording of ADI-002 in `technical-requirements.md` presupposed a database that this project is not building for V1.
- **No index at all, scan files directly at query time.** Rejected as a target design (see correction above) — only viable as a short-lived bootstrapping step while the item count is still small, not as the V1 plan.
- **Index file stored inside the Obsidian vault.** Rejected: gets caught in vault sync, and risks multi-device write conflicts on a file that isn't even meant to be shared data — see decision above.
- **A shared, server-based index for real-time multi-device querying.** Rejected for now: not supported by any current use case, and would reintroduce the operational overhead ADI-001 explicitly avoided. Left open for a future ADR if the need becomes real.

## Consequences

- Retrieval quality and performance are fully decoupled from the canonical storage decision (ADI-001) — the index can evolve independently (from simple keyword scan to embeddings-based semantic search) without ever touching canonical files.
- Because the index is derived and rebuildable, there is no risk of it becoming a second source of truth as long as this boundary is respected during implementation (Phase 2/3 tickets touching retrieval should make this explicit).
- Each device maintains its own index copy — if Cleo searches from a device she hasn't used in a while, its index may be stale until Pekopeko rebuilds/catches it up against the (already-synced) vault. This is a minor UX detail for Phase 2/3 to handle (e.g., rebuild-on-launch if the vault's changed since last run), not an architectural problem.
