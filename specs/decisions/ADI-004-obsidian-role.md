# ADI-004: Obsidian's Role Relative to Canonical Knowledge

- **ID**: ADI-004
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`technical-requirements.md` (section 23) asks how Obsidian should interact with canonical knowledge, citing AP-001 and CAP-CORE-001. This decision was already substantially shaped by ADI-001 (see `specs/decisions/ADI-001-canonical-persistence-model.md`): canonical knowledge is stored as structured files, backed up and synced across devices via a directory sync tied to an Obsidian vault. That means the vault relationship is not a fully open question — the remaining scope is exactly how Obsidian's vault functions relative to that canonical storage, and how the internal file organization is structured.

Cleo explicitly deprioritized browsing convenience for this decision: she does not need the vault to be pleasant or curated for daily reading, only technically correct and occasionally accessible if needed. This materially simplifies the decision — there is no need to balance technical design against a nice reading experience.

## Decision

**The Obsidian vault root is Pekopeko's canonical storage root.** It is not a mirror, export target, or separate curated view — it is the same file tree established in ADI-001. Obsidian is treated as a generic, off-the-shelf viewer/editor operating on these files; Pekopeko does not depend on Obsidian being installed, running, or having a current cache for any of its own functionality.

**Internal organization**, chosen for machine/tooling clarity rather than visual browsing comfort:
- Top level: one folder per domain (PERSONAL, FICTION, LEARNING, RESEARCH, PUBLISHING), directly implementing Domain Isolation (AP-005) — domain membership is enforceable as a path prefix.
- Within each domain: one subfolder per item type (entities, assertions, events, relationships, proposals).
- Within each item: the per-item history subfolder established in ADI-001 (superseded versions).

**Frontmatter is unabridged.** All structured fields (ID, type, domain, temporal validity, lifecycle status, epistemic status, provenance, relationship endpoints, etc.) live fully in each file's YAML frontmatter — no attempt to hide or curate fields for readability, since that is not a stated need.

**Obsidian's native features (graph view, backlinks, full-text search, plugins) are never relied upon for Pekopeko's own functionality.** Retrieval (ADI-002) and relationship traversal (ADI-003) are Pekopeko's own derived indexes, independent of whether Obsidian is open or its cache is current. Obsidian's built-in views are an incidental convenience for whenever Cleo does look directly at the vault, never a dependency.

**Relationships are not duplicated as Obsidian wikilinks.** They exist once, as the structured records established in ADI-003. Given no browsing-convenience requirement, a second representation to keep in sync would add complexity without a corresponding benefit.

**Writes to canonical files must be atomic** (write to a temporary file, then rename into place). The same files are concurrently watched by the Obsidian app and by Cleo's sync tool, in addition to being edited by Cleo directly and written by Pekopeko's own processes (e.g. an ingestion pipeline creating new entity files) — atomic writes reduce the risk of any of these readers observing a partially-written file.

## Alternatives considered

- **A separate, curated "pretty" vault distinct from Pekopeko's technical canonical storage, kept in sync with it.** Rejected: adds a second representation to maintain, contradicts the canonical/derived simplicity established in ADI-006, and isn't needed given Cleo's explicit priority (occasional, not-necessarily-convenient access is sufficient).
- **Relying on Obsidian's native graph/backlink/search as Pekopeko's actual retrieval or traversal mechanism.** Rejected: would couple core system functionality to a third-party application being installed, open, and current — directly against the derived/rebuildable-by-Pekopeko-itself principle in ADI-002 and ADI-003.
- **Duplicating relationships as both structured frontmatter and Obsidian wikilinks.** Rejected: no browsing-convenience requirement justifies the added drift risk of two representations of the same fact.

## Consequences

- Domain folders and per-item history subfolders are visible in Obsidian's file browser, not hidden — acceptable since hiding them for tidiness isn't a priority.
- Pekopeko needs its own file-writing discipline (atomic writes) because it shares the vault folder with two other active writers/watchers (the Obsidian app, the sync tool), not just with Cleo's manual edits.
- If priorities change later (e.g., a nicer view becomes desirable), that should be a new or amended ADR — this one explicitly deprioritizes it based on Cleo's current, explicit stance, not a permanent assumption.
