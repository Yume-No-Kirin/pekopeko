# ADI-001: Canonical Persistence Model

- **ID**: ADI-001
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16, after review of the historization mechanism specifically — see correction below)

## Context

`technical-requirements.md` (section 23, Architectural Decision Inputs) requires determining "an appropriate canonical persistence model for structured knowledge," citing AP-001 (knowledge representation must support entities, assertions, events, relationships, temporal information) and all 18 use cases.

Relevant product context (re-read in full before drafting this ADR, per the continuity discipline in `docs/ROADMAP.md`):
- `specs/product/product-model.md`: the target user is a single individual, not a multi-user or enterprise system.
- `specs/product/scope.md`: "No final database technology has been selected... No final vector database has been selected... No graph database has been selected," and lists "Final database schema design" and "Production-grade performance optimization" as explicitly out of scope for the current phase.
- `specs/product/non-goals.md`: "Choosing implementation technologies during the product-definition phase" and "Designing the final architecture before the product and domain models are understood" are explicit non-goals. "Implementing any specific database, vector store, or other technology choices at this product definition stage" is an explicitly rejected direction.
- `specs/product/user-needs.md`: primary needs are about reliable organization, provenance, and control — no stated requirement for large-scale volume or concurrent multi-user access.

**Correction (2026-08-16, added after initial drafting):** the first draft of this ADR did not yet reflect a full read of `specs/product/use-cases.md`. That document's "Architectural Pressure Points" section lists "Large-Scale Review — Managing hundreds of thousands of proposals efficiently" as a technically demanding capability, and its "Potential Gaps" section separately notes "no explicit consideration of performance scaling requirements for very large knowledge bases or high-volume ingestion scenarios." This is a real volume signal that the product-level docs alone did not surface, and it should have been part of this decision's context from the start. It does not change the decision below — files remain viable as canonical storage at that scale, since a sharded directory layout handles hundreds of thousands of small files without difficulty — but it directly raises the bar for ADI-002 (see that ADR's own correction).

**Correction (2026-08-16, second revision, after discussion with Cleo):** the canonical file tree is **not** versioned via git. Cleo's actual usage pattern is a continuously, live-edited personal knowledge base ("second brain," thousands of notes), backed up and synced across devices via a directory sync tied to an Obsidian vault (Obsidian Sync or an equivalent) — not a git-managed repository. Running git alongside a live, continuously-syncing third-party tool on the same files is a real source of conflict: both systems independently manage the same files, `.git` metadata would sync pointlessly across devices, and concurrent edits from sync + git risk corrupting either. Historical state preservation (AP-004, and HIR-001 through HIR-010 in `technical-requirements.md`, none of which specify a mechanism) is therefore implemented at the file/data level instead of via version control — see Decision below, which was revised accordingly.

## Decision

Canonical knowledge is stored as structured files, not a database. One file per knowledge item (entity, assertion, event, relationship, proposal), in a consistent structured format (e.g. YAML frontmatter for structured fields — ID, type, domain, temporal validity, epistemic status, lifecycle status, provenance — plus a body for free-text content). Files are organized under domain-scoped directories, directly supporting Domain Isolation (AP-005). Every item has a stable, unique identifier that is referenced explicitly wherever it is used — never implied by position or filename alone.

Historical state preservation (AP-004, HIR-001..010) and part of provenance tracking (AP-003) are implemented at the file level, not via git or any version-control system:
- Each item's file holds its current, `ACTIVE` state.
- When it changes, the complete previous version (full content, not a diff) is copied into a per-item history subfolder — e.g. `<item-type>/<item-id>/history/<timestamp>--v<n>.md` — with its own `lifecycle_status: SUPERSEDED` and a pointer to whatever superseded it.
- This is grounded directly in two use cases: UC-010 (Correction Propagation), where the original assertion is explicitly "marked as superseded" — a real state, not a log line — and UC-015 (Knowledge Change History), whose query pattern ("what did Pekopeko know about Character X six months ago") requires retrieving a full past state directly, not reconstructing one by replaying a sequence of field-level diffs.
- Full snapshots kept this way stay addressable and human-inspectable (plain text, openable directly) without requiring git or any VCS layered onto an actively-synced vault.

Backup and cross-device redundancy are handled entirely by Cleo's existing Obsidian vault sync mechanism, outside Pekopeko's own architecture — that is a backup concern, separate from the historization concern above, and Pekopeko does not need to build or manage it.

No database (relational, document, or graph) is part of the canonical store for V1.

## Alternatives considered

- **SQLite as canonical store.** Rejected for V1: ties canonical state to a binary format that is harder to inspect and edit directly than plain files, and offers no benefit over files at the target scale (single user, no stated volume requirement).
- **PostgreSQL as canonical store.** Rejected for V1: introduces real operational overhead (a running service to install/maintain/back up) not justified without a confirmed need for concurrent multi-device write access. Also conflicts directly with `non-goals.md`'s rejection of choosing implementation technologies at this stage.
- **Hybrid (start on SQLite, design for an easy migration to PostgreSQL later).** Considered and rejected in favor of files: it still commits to a database technology now, and plain files are strictly more inspectable and easier to reason about by hand than SQLite for a personal, human-in-the-loop system whose primary value is trustworthiness and traceability.
- **Git-based historization of the canonical file tree.** Initially proposed, then rejected after discussion with Cleo: conflicts with a live, continuously-synced Obsidian vault (see correction above). Kept here for the record rather than silently dropped.
- **Frontmatter changelog only (field-level diffs, no full snapshots).** Rejected as the primary mechanism: doesn't satisfy UC-015's need to retrieve a full past state directly, and would bloat a frequently-revised note's frontmatter over years of edits. May still be useful as a lightweight *summary* of what changed at each version, layered on top of the full-snapshot mechanism — not a replacement for it.

## Consequences

- Directly shapes ADI-002 (retrieval), ADI-003 (relationship model), ADI-004 (Obsidian's role — the per-item history subfolders must coexist sensibly with how Cleo browses her vault), and ADI-006 (persist vs. recompute) — see their respective ADRs, which build on this one.
- Requires discipline in ID design now: identifiers must be stable and explicit so that any future migration to a database is a mechanical import script, not a redesign.
- Concurrent writes from multiple internal agents/processes are not automatically safe the way a transactional database would make them — a single-writer discipline or explicit file locking must be designed before Phase 3 implementation touches this, not assumed away.
- This does not rule out introducing a database later — as a derived/rebuildable index (see ADI-002/ADI-003), or eventually as the canonical store itself if scale or multi-device needs materialize. If that happens, it should be recorded as a new ADR that supersedes this one, not a silent architecture drift.
