# ADI-003: Relationship Model

- **ID**: ADI-003
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`technical-requirements.md` (section 23) asks "whether the conceptual relationship model requires a graph database or merely graph-like structures," citing AP-001 and CAP-CORE-009 (Relationship Traversal, RQR-001..006). As with ADI-002, this decision follows directly from ADI-001 (see `specs/decisions/ADI-001-canonical-persistence-model.md`): canonical storage is files, so a graph database (which would itself be a database) is not part of canonical storage by construction.

## Decision

Relationships are stored as structured records within the canonical files, each explicitly naming its endpoints by their stable item IDs (per ADI-001), its type, temporal validity, and provenance — matching the conceptual "Relationship" definition in `specs/domain/knowledge-model.md`. No dedicated graph database is introduced for V1. Traversal is served by a derived adjacency structure built from these relationship records — the same status as the retrieval index in ADI-002: derived, rebuildable from the canonical files, never itself canonical, and following the same storage rule as ADI-002's index — never persisted inside the Obsidian vault (to avoid the same sync-conflict risk), built per-device from the synced canonical files.

## Alternatives considered

- **Dedicated graph database.** Rejected for V1 for the same reasons as in ADI-001: it would be a database commitment not justified at the expected personal-use scale, and conflicts with the same non-goals around premature technology selection.
- **Graph-like structures inside a primary database.** Moot given ADI-001 — there is no primary database.

## Consequences

- If relationship traversal performance ever becomes a genuine bottleneck at real scale, a graph database could be introduced purely as an additional derived index (like the retrieval index), without changing canonical file storage. That would warrant a new ADR rather than a silent change.
- Relationship records must consistently reference stable IDs (never embed another item's full content) — this is what makes the derived adjacency structure buildable from files alone.
