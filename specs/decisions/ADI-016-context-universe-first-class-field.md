# ADI-016: Context/Universe as a First-Class Field (amends ADI-012)

- **ID**: ADI-016
- **Date**: 2026-09-06
- **Status**: Accepted (confirmed by Cleo on 2026-09-06, while scoping TASK-014a/TASK-014b)

## Context

`docs/OPEN-ISSUES.md` carried an open entry (added 2026-09-06, the same day this ADR was written)
titled "Pas d'isolation 'Context/Universe' à l'intérieur du domaine FICTION." It pointed out that
`specs/domain/knowledge-model.md:45-46` has long defined a "Context / Universe" concept — "a
specific instance or setting within a domain," e.g. "in the FICTION domain, different novels or
shared fictional universes would be contexts" — and that `specs/product/use-cases.md` UC-018
("Fictional Universe Isolation") describes exactly this scenario: two novels, each with a character
named "Alex," expected to stay distinguishable. Nothing in the codebase implements this: no
`context`/`universe`/`project` field exists anywhere, and the only organizing mechanism inside a
domain is ADI-012's free-form, LLM-proposed folder-path taxonomy (`proposed_path_segments`) —
useful for browsing, but not an enforced boundary, and scoped to `assertion` only.

This surfaced directly while scoping a new ticket: Cleo asked for a ticket that derives a folder
segment from an ingested file's source-folder location (e.g. `fiction/tatouages/plot.md` → context
`tatouages`, a novel's code name) to organize canonical notes. Per AGENTS.md's rule that an open
issue bearing on a ticket's scope must be surfaced rather than silently resolved one way, this was
brought back to Cleo before drafting the ticket — same sequencing as ADI-012 being decided before
TASK-014's ticket text.

Two things were confirmed directly with Cleo in that conversation:

1. `context` should be a real, first-class, queryable field — not merely a folder-naming
   convention indistinguishable from ADI-012's free taxonomy segments.
2. Because the open issue's own motivating example is a **character** (an entity) reused across
   two novels, an assertion-only `context` (mirroring ADI-012's own assertion-only scope for
   `proposed_path_segments`) would miss the actual case this is meant to address. `context` must
   apply to all four canonical item types: assertion, entity, event, relationship.

**Checked against the current code before deciding what this ADR can honestly promise**: no entity
dedup or name-matching logic exists anywhere in `src/app` — `review/storage.py::_generate_entity_id()`
(and its assertion/event/relationship siblings) always mints a fresh UUID; nothing compares an
incoming entity against existing ones. The open issue's "two homonymous characters could get merged
during dedup/entity resolution" risk therefore has no existing mechanism to make context-aware —
that half of the issue stays open, pointed at TASK-029 (Fiction Module V1, still un-ticketed,
`specs/tasks/BACKLOG-CLAUDE.md` §5), not silently declared fixed by this ADR.

## Decision

**`context: Optional[str] = None` becomes a first-class frontmatter field on all four canonical
item types** (assertion, entity, event, relationship) — `None` means no context applies; never an
empty string, matching this project's existing `None`-vs-`[]` conventions (e.g. `valid_until`).

**Physically reflected in the path**, consistent with ADI-012's own "the chosen path is the real
location, not a cosmetic layer" philosophy:

```
Assertion:                <domain>/assertions/<context>/<segment_1>/.../<segment_n>/<id>/<id>.md
Entity/Event/Relationship: <domain>/<type-plural>/<context>/<id>/<id>.md
```

`context: None` produces exactly today's path for every type — full backward compatibility, same
guarantee every prior amendment in this chain has preserved. For entity/event/relationship, no
free taxonomy segments exist yet (ADI-012 deferred those to whenever TASK-005/012's own layout
work is revisited) — `context` is the only new path component for those three types, independent
of that still-open gap.

**`context` is distinct from `proposed_path_segments`**: it is a single, stable, queryable
identifier (a novel's code name, a life-area name) — not one more free taxonomy level a reviewer
can nest arbitrarily. `_COMMON_EDITABLE_FIELDS` (`review/storage.py:58`) gains `"context"`
directly, applying to all four types uniformly — a deliberate departure from `proposed_path_segments`'s
own type-scoped allow-list, because `context` is cross-type by design rather than staying
assertion-only.

**Derivation granularity: once per source note, not per item.** `proposed_path_segments` is
deliberately per-assertion (ADI-014, so a note's assertions can land in different thematic
folders); `context` is the opposite — a novel's code name or a life-area doesn't vary between the
entities/events/assertions extracted from the same note. `context` is computed once per
`ingest_source`/`extract_source` call and applied identically to every item that call produces.

**Genuinely optional — no forced non-null fallback.** ADI-014 made the taxonomy path mandatory
(`["uncategorized"]` if nothing better is found) because a reviewer needs *some* folder to look in.
`context` has no equivalent forcing requirement: a note with no folder signal and no confident
LLM guess simply gets `context: None`, and that is a correct, non-degraded outcome, not a failure
mode to patch over.

**Scoped existing-folder scan (assertion only).** `scan_existing_assertion_folders`/
`scan_proposed_path_segments` (`ingestion/storage.py`, ADI-014/015) gain an optional
`context: Optional[str] = None` parameter; when given, the scan is restricted to
`<domain>/assertions/<context>/` instead of the whole domain. Default `None` preserves today's
whole-domain scan exactly. This is the concrete fix for the open issue's own observed symptom —
"the folders of novel A currently influence the suggestions made for novel B" — for the one type
that has such a scan mechanism at all.

**What this ADR does not do, stated explicitly rather than left implicit:**

- **No entity/relationship dedup-by-context.** No dedup/matching mechanism exists in this codebase
  for any item type today (verified above) — there is nothing to scope by context. This remains
  open, owned by whenever entity resolution itself is designed (TASK-029).
- **No taxonomy segments for entity/event/relationship.** `proposed_path_segments` stays
  assertion-only, exactly as ADI-012 already decided — this ADR does not retroactively extend it.
- **No existing-context-folder scan for entity/event/relationship.** No scan mechanism of any kind
  exists for those types today (unlike assertions, which already had one from ADI-014/015) — there
  is nothing to add a `context` parameter to.
- **No change to how `context`'s *value* gets populated** — that mechanism (source-folder location,
  LLM fallback) is TASK-014b's own scope, a separate ticket from the structural change this ADR
  authorizes (TASK-014a), mirroring how ADI-012 (structure) and TASK-001e (LLM value-population)
  were already two separate tickets for `proposed_path_segments`.

The `docs/OPEN-ISSUES.md` entry that raised this question is removed once this ADR and its two
implementing tickets (TASK-014a, TASK-014b) exist, per that file's own stated convention that a
settled entry migrates to its real destination rather than staying marked `[fermé]` — the residual
entity-dedup gap is preserved above rather than lost with it.

## Alternatives considered

- **Folder-path convention only, no dedicated field** (the open issue's other framed option): treat
  a chosen folder segment as sufficient, with no distinct `context` frontmatter key. Rejected:
  indistinguishable from an ordinary taxonomy segment, not reliably queryable/scannable, and does
  nothing to let a future dedup mechanism scope itself by context — it would just be one more
  string in a free-form path.
- **Assertion-only scope**, mirroring `proposed_path_segments`. Rejected by Cleo directly: the
  open issue's own motivating example (a homonymous character reused across two novels) is an
  entity, not an assertion — an assertion-only field would not address the case that motivated it.
- **Per-item derivation** (matching `proposed_path_segments`'s own per-assertion granularity).
  Rejected: a novel's identity or a life-area doesn't vary between items extracted from the same
  note; per-item derivation would be needless extra LLM calls for a value that should be constant
  across one extraction/ingestion run.
- **Forced non-null fallback**, matching ADI-014's mandatory-path guarantee. Rejected: unlike a
  taxonomy path (which a reviewer needs to browse by), a note genuinely not belonging to any
  distinct project/universe is a normal, common case — forcing a fallback value here would
  manufacture false context where none exists.
- **Solving entity dedup-by-context now**, to fully close the open issue's stated risk. Rejected as
  out of scope: no dedup/matching mechanism exists yet for any item type; building one only to make
  it context-aware would be substantially larger than what was asked, and belongs to TASK-029's own
  future scope once that ticket exists.

## Consequences

- `review/storage.py`: `assertion_path`/`entity_path`/`event_path`/`relationship_path` and their
  `write_*_file` counterparts each gain an additive, optional `context` parameter (TASK-014a).
  `accept_proposal` (`review/pipeline.py:239-321`) reads `context` from the accepted proposal's
  frontmatter in all four of its type branches. `_COMMON_EDITABLE_FIELDS` gains `"context"`.
- `ingestion/storage.py`'s two existing-folder scan functions gain an optional `context` parameter
  (TASK-014a, assertion-only, additive).
- `ingestion/providers/base.py::ExtractedAssertion` and `extraction/providers/base.py`'s
  `ExtractedEntity`/`ExtractedEvent`/`ExtractedRelationship` each gain a new `context: Optional[str]
  = None` field; `ingestion/providers/ollama_provider.py` and `extraction/providers/ollama_provider.py`
  each gain their own independent derivation logic (TASK-014b) — no shared import between the two
  modules, consistent with the module-independence discipline TASK-002 established and
  `scan_existing_assertion_folders` already follows for its own independent reimplementation.
- **Known limitation, accepted rather than solved**: `ingestion/` and `extraction/` run as two
  independent pipelines over the same source note. The folder-derived context will always agree
  between them (a deterministic function of `source_path`), but the LLM-guess fallback used when no
  folder signal exists could, in principle, diverge between the two pipelines for the same note.
  Not corrected here — flagged the same way ADI-014/015 flagged their own known, unfixed
  limitations rather than silently ignoring them.
- Frontend: entity/event/relationship gain their first path-related display at all (a `context`
  chip) — TASK-012 gave them `EntityTypeBadge`/`EventTemporalRange`/`RelationshipEndpoints` but no
  folder-path element, since ADI-012 never applied to them. `FolderPathBuilder.jsx` itself stays
  assertion-taxonomy-specific; `context` gets its own small, type-agnostic display/edit component
  (TASK-014a) rather than being grafted onto a component built for a different, still
  assertion-only concept.
- This does not touch ADI-002 (retrieval) or ADI-003 (relationship model) — both remain derived/
  reconstructible and unaware of physical folder taxonomy, same as ADI-012 already established.
