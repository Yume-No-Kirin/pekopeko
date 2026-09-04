# ADI-012: Folder-Path Organization (amends ADI-004)

- **ID**: ADI-012
- **Date**: 2026-09-04
- **Status**: Accepted (confirmed by Cleo on 2026-09-04, while scoping TASK-014)

## Context

`specs/ux-design/` (README, section "Interactive Folder Path Builder"; `pekopeko-workflow.html`
and `pekopeko-proposal-detail.html`) shows a UI element — `[segment ▼] / [segment ▼] [+ Ajouter]`
— that lets the reviewer place an accepted note under a taxonomy path she chooses, e.g.
`mythologie/japonaise/créatures/kitsune-transformation`. No ticket has implemented this yet:
TASK-010/TASK-011 (both `completed`) explicitly stayed on the fixed canonical path from
ADI-004 (`<domain>/<item-type-plural>/<item-id>/<item-id>.md`, reused literally by TASK-002's
`assertion_path` and TASK-005's still-`backlog` file-layout contract), deferring the builder to
`BACKLOG-CLAUDE-V2.md`'s TASK-014 entry — "Organisation en dossiers (folder-path builder) ...
au-delà du chemin fixe `<domain>/<type>/<id>/`".

Writing TASK-014's ticket required first answering a question ADI-004 left open on purpose: does
the chosen path change *where the canonical file physically lives*, or is it separate metadata
layered on top of the fixed path? ADI-004 itself anticipates exactly this fork: "If priorities
change later (e.g., a nicer view becomes desirable), that should be a new or amended ADR — this
one explicitly deprioritizes it based on Cleo's current, explicit stance, not a permanent
assumption." This ADR is that amendment, decided with Cleo before TASK-014 was drafted rather
than assumed inside the ticket.

## Decision

**The chosen folder path physically relocates the canonical file.** It is not a separate
metadata field layered on an unchanged fixed location — the file is written where the path says,
exactly as the mockup's own accept-confirmation text implies (`${folderPath}/assertions/
assert-[uuid]/assert-[uuid].md`).

The new canonical path, replacing the fixed layout ADI-004 defined for the item types this
applies to:

```
<vault_root>/<domain>/<item-type-plural>/<segment_1>/.../<segment_n>/<item_id>/<item_id>.md
```

Three constraints, each confirmed explicitly by Cleo rather than inferred from the mockup alone:

1. **`<domain>` stays the fixed first segment**, exactly as ADI-004 already established (Domain
   Isolation, AP-005, enforceable as a path prefix) — the builder never edits it. This differs
   from the mockup's literal example, where the shown path (`mythologie/japonaise/...`) has no
   visible relationship to the `domain: FICTION` metadata shown next to it; that ambiguity is
   resolved here in favor of keeping domain a hard prefix.
2. **`<item-type-plural>` stays directly under `<domain>`**, before any custom segment —
   preserving ADI-004's original machine-clarity reasoning (a glob like `<domain>/assertions/*`
   must keep working without walking an arbitrary taxonomy tree first). Custom segments nest
   *inside* the type folder, not above it.
3. **`segment_1..n` defaults to empty.** An item with no chosen segments writes to exactly the
   path ADI-004 already produces today (`<domain>/<item-type-plural>/<item-id>/<item-id>.md`) —
   full backward compatibility with every file already on disk and with TASK-002's existing,
   unmodified behavior when no segments are supplied.

**Scope: `assertion` only, for now.** TASK-014 (which this ADR unblocks) is scoped
assertion-only, matching the same MVP boundary TASK-010/011/013 already use. `entity`/`event`/
`relationship` (TASK-005, TASK-012 — both still `backlog`, never implemented) are **not**
amended by this decision yet: their canonical writers, once implemented, must adopt this same
layout (see Consequences) rather than the plain fixed layout TASK-005's current ticket text
still cites, but that adoption is that future ticket's own work, not retroactively done here.

**Segment naming convention** (not a hard server-side guarantee unless a ticket implementing
this ADR says so explicitly): a segment is a single non-empty path component, no `/` and no
`..` — same intent as the mockup's own client-side cleanup (`trim().toLowerCase().replace(/\s+/g,
'-')`), reused as a convention rather than re-derived.

**Origin of the initial, pre-review path.** The path segments shown to a reviewer before any
edit are proposed by the extraction LLM at ingestion/extraction time, not left empty by default.
This reopens the (already `completed`) extraction pipelines additively — same posture already
established by TASK-001a/TASK-001b/TASK-001c/TASK-001d for other gaps found while wiring a
mockup to real data: a satellite ticket adds the field, degrading to an empty list if the
provider doesn't supply one, never blocking or changing an existing public signature.

## Alternatives considered

- **Metadata-only field, no physical relocation** (e.g. an `organization_path` frontmatter
  field on an otherwise unmoved canonical file). Consistent with ADI-002/ADI-003's own pattern
  of never physically duplicating anything derived into the vault, and would have avoided
  amending ADI-004 at all. Rejected by Cleo in favor of physical relocation — the folder
  structure itself is meant to be a real, Obsidian-visible organization the reviewer builds, not
  just a searchable tag.
- **Custom segments directly under `<domain>`, with the item-type folder nested inside them**
  (`<domain>/<segments...>/<item-type-plural>/<id>/<id>.md`), matching the mockup's literal
  example string more closely. Rejected: would lose ADI-004's original machine-clarity property
  (no more direct `<domain>/assertions/*` glob) for a benefit (closer fidelity to one example
  string in a static mockup) Cleo judged not worth that cost.
- **Domain not enforced as a fixed segment**, letting the builder construct a path fully
  independent of `domain` (as the mockup's literal markup suggests, where the shown path has no
  visible domain prefix). Rejected: breaks Domain Isolation's path-prefix enforceability
  (AP-005), which every prior ADR in this corpus treats as load-bearing.

## Consequences

- TASK-002 (`completed`) needs an additive amendment: `assertion_path`/`write_assertion_file`
  gain an optional `path_segments` parameter, defaulting to none — see TASK-014's own ticket for
  the exact scope. This is the same category of change TASK-001a/b/c/d already made to
  TASK-001/TASK-003's completed code.
- TASK-005 (`backlog`, never implemented) currently cites the old fixed layout literally in its
  own "File layout (exact contract)" section. A short note has been added there pointing at this
  ADR (see that ticket) — TASK-005 is not rewritten here, since implementing entity/event/
  relationship support for this layout is explicitly out of TASK-014's scope and remains future
  work.
- A new satellite ticket (TASK-001e) is required for the extraction pipelines to propose an
  initial path — see that ticket for its own scope and constraints.
- Obsidian's file browser will show these nested taxonomy folders directly (same consequence
  ADI-004 already accepted for domain/type/history folders) — no new visibility concern beyond
  what ADI-004 already decided.
- This does not touch ADI-002 (retrieval) or ADI-003 (relationship model) — both remain derived/
  reconstructible and unaware of physical folder taxonomy, same as before.
