# ADI-006: Persistence vs. Recomputation

- **ID**: ADI-006
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`technical-requirements.md` (section 23) asks "what should be persisted vs recomputed," citing AP-001 and CAP-CORE-001. This follows directly from ADI-001, ADI-002, and ADI-003 (see the corresponding files in `specs/decisions/`), which already establish a canonical/derived split for storage and retrieval.

## Decision

The only persisted, canonical data is the file tree of knowledge items established in ADI-001, including its per-item history subfolders (superseded versions — see ADI-001's historization mechanism, which does not use git). Everything else is treated as derived and recomputable, including: the retrieval index (ADI-002), the relationship adjacency structure (ADI-003), aggregate or dashboard views over knowledge health, and derived knowledge produced by reasoning/analysis over canonical items (per the "Derived Knowledge" concept in `specs/domain/knowledge-model.md`). All of these can be deleted and rebuilt from the canonical files at any time without permanent data loss.

## Alternatives considered

- **Persist derived artifacts as if canonical** (e.g., treat a computed index as authoritative). Rejected — this would create a second source of truth that can silently drift from the canonical files, undermining the traceability and integrity principles in `specs/product/product-model.md`.

## Consequences

- Keeps canonical storage simple, small, and fully inspectable with plain-text tools (a text editor, `diff`, `grep`) — no VCS required to read or compare states.
- Derived artifacts may still be cached on disk for performance (e.g., a persisted index file) — "recomputable" does not mean "never written to disk," it means "safe to delete and rebuild without data loss." Phase 2/3 tickets should distinguish these two senses explicitly.
- If, during implementation, something currently classified as "derived" turns out to be impossible to cleanly rebuild from the canonical files alone, that is a signal it should actually be canonical — worth flagging rather than working around silently.

## Why this scales (explicit answer, recorded 2026-08-16 at Cleo's request)

This canonical/derived split is what makes later evolution toward a database, a graph store, or vector search low-cost rather than a redesign — worth stating explicitly since it will come up again:

- **Adding a derived index (a database for search, a graph structure for relationships, a vector index for semantic search) is cheap by construction.** These are all "derived" per this ADR — additive, disposable, rebuildable from canonical files. None of them require touching or migrating the canonical file tree established in ADI-001. This is true today and stays true as more derived layers are added (ADI-002's SQLite/FTS5 → vector index path, ADI-003's potential future graph index, are both instances of this).
- **Migrating canonical storage itself to a database, if that ever becomes necessary, is explicitly claimed in ADI-001 to be "a mechanical import script, not a redesign."** That claim has exactly one precondition, and it is not automatic: item IDs must actually stay stable and explicit throughout implementation — every relationship and reference must point to an ID, never duplicate content or rely on implicit position/filename. If Phase 3 implementation drifts from that discipline, this claim stops holding. This should be treated as a concrete constraint to uphold (and ideally test for) during implementation, not an architectural guarantee that enforces itself.
- **Distinction to keep in mind:** adding a derived index is genuinely near-free (delete and rebuild at will). Migrating canonical storage to a database — if the need ever becomes real — remains a real, well-scoped migration project (write the import, verify integrity, cut over), not a zero-cost operation. It is bounded and mechanical rather than a rewrite, which is the actual guarantee here — not instant or free. Per ADI-001's Consequences, that migration should be recorded as a new ADR superseding ADI-001, not a silent drift.
