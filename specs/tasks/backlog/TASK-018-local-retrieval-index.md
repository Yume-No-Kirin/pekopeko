# TASK-018: Local Retrieval Index (SQLite/FTS5, V1)

- **Status**: backlog

## Objective

Implement ADI-002 (`specs/decisions/ADI-002-retrieval-system.md`) for the four canonical item
types — full-text search over `assertion`/`entity`/`event`/`relationship` files, via a local
SQLite/FTS5 index that is derived, reconstructible, and never stored inside the Obsidian vault.
Delivered directly as SQLite/FTS5 in this ticket, skipping ADI-002's intermediate "V1 in-memory at
startup" rollout step (see V1 scope decisions below). **Three deviations from ADI-002 as written,
named here rather than folded into "only the staging order is skipped"** (correction 2026-09-07,
consistency review — the earlier wording understated them):

1. The intermediate in-memory rollout step is skipped. Uncontroversial: ADI-002's destination
   (a local, derived, rebuildable SQLite/FTS5 index outside the vault) is unchanged.
2. **This ticket is not incremental.** ADI-002's step 2 specifies the FTS5 index is "updated
   incrementally as files change rather than fully rescanned each time"; this ticket does a full
   rebuild at process startup instead (see V1 scope decisions). What ships is therefore step 2's
   *storage* with step 1's *refresh strategy* — a real, deliberate halfway point, not step 2.
3. **`proposals/` are not indexed.** ADI-002 states the index is "required infrastructure for the
   **review queue** and search from early in V1", justified explicitly by the "hundreds of
   thousands of proposals" pressure point (`specs/product/use-cases.md`, Architectural Pressure
   Points §7). This ticket serves *search over canonical items* only; the review queue keeps
   TASK-010's client-side filtering over a `limit=500` fetch. ADI-002's review-queue rationale is
   therefore still unaddressed after this ticket — see TASK-015's own note on the same gap.

None of the three is treated as an ADI-002 amendment: the architectural decision (derived, local,
never-in-vault, rebuildable) holds in all three cases. They are V1 scope reductions, and they are
Cleo's to accept or refuse at read time. Closes CAP-CORE-010/RTR-001's full-text-search and domain-specific-filtering
requirements (`specs/architecture/capabilities.md`, `specs/architecture/technical-requirements.md`)
— RTR-001's semantic-search and relationship-based-navigation requirements remain future work per
ADI-002 itself (steps 3 and out-of-scope respectively).

Fills the gap TASK-007 explicitly left open: its own "Out of scope" section states "Retrieval
endpoints — TASK-018 (backend)/TASK-019 (frontend)". Written directly at Cleo's request rather
than in strict backlog order — TASK-015 remains the next ticket scheduled for *implementation*
(see `docs/ROADMAP.md`).

New code only: a new `src/app/retrieval/` package plus one new API blueprint. No modification to
any `completed` ticket's code (`ingestion/`, `extraction/`, `review/`, `config/`, `api/`'s existing
routes) — this ticket only adds a reader over files those packages already write, and one new
route file.

## Binding context (references, not duplicated here)

- **ADI-002** (retrieval-system, Accepted): the index is a derived, reconstructible cache over
  canonical files, never inside the vault, never authoritative — this ticket implements that
  decision's ultimate SQLite/FTS5 form directly (see V1 scope decisions for why the in-memory
  staging step is skipped).
- **ADI-001** (canonical-persistence-model, Accepted): canonical items live as per-item folders
  under `<domain>/<type>/<id>/<id>.md` with YAML frontmatter + Markdown body — confirmed live in
  `src/app/review/storage.py` (`assertion_path`/`entity_path`/`event_path`/`relationship_path`).
  This ticket's scanner reads that exact layout, read-only.
- `specs/architecture/capabilities.md` CAP-CORE-010 (Knowledge Search and Retrieval) /
  `specs/architecture/technical-requirements.md` RTR-001 (full-text + domain-specific filtering,
  in scope here; semantic search and relationship-based navigation, out of scope here).
- `specs/domain/knowledge-invariants.md`:
  - INV-008/INV-009 (domain isolation / explicit cross-domain ops): every search is scoped to one
    `domain`, required, never inferred — same posture as every existing endpoint.
  - INV-011 (a derived representation is never the canonical model): the index carries no
    authority; deleting it and rebuilding from the canonical files loses nothing.
- TASK-007/TASK-007a (`completed`): this ticket's endpoint reuses their conventions verbatim —
  Flask blueprint registration in `src/app/api/app.py`, `X-API-Key` check, the
  `{"error": {"type", "message"}}` envelope, `127.0.0.1`-only binding, and TASK-007a's
  `parse_pagination_args`/`paginate` helpers in `src/app/api/serialization.py`.
- `src/app/config/schema.py` (TASK-004, `completed`): `RetrievalConfig.index_dir` already exists
  in `PekopekoConfig`, with env override `PEKOPEKO_RETRIEVAL_INDEX_DIR` already wired in
  `src/app/config/loader.py`, and already surfaced read-only via `GET /config`
  (`src/app/api/serialization.py`, `data["retrieval"]["index_dir"]`). This ticket **consumes**
  that existing, previously-reserved-but-unused config field — it does not add a new one.

## Scope

1. New package `src/app/retrieval/`:
   - `scanner.py` — read-only walk of `<vault_root>/<domain>/{assertions,entities,events,
     relationships}/**/<id>.md`, parsing each file's frontmatter + body via its own small
     frontmatter parser (re-implemented here, not imported from `review.frontmatter` — same
     module-independence discipline `review/storage.py`'s own docstring already documents for
     itself relative to `ingestion/storage.py`: only the on-disk contract is shared, not code).
     `proposals/`, `sources/` and **every `history/` subfolder** are never walked (see V1 scope
     decisions). The `history/` exclusion is load-bearing, not incidental: a per-item
     `history/<timestamp>--v<n>.md` snapshot (ADI-001, written by TASK-006's `edit_proposal`)
     carries `lifecycle_status: SUPERSEDED` and a body that is a *previous* version of a live
     item — indexing it would make every edited item appear several times in search results, with
     stale text. Filtering on "filename stem equals its parent directory name" already excludes
     them by construction, but the exclusion must be explicit and directly tested (AC12), not left
     as a side effect of the glob's shape.
   - `index_store.py` — SQLite/FTS5 schema and low-level access:
     - A virtual table `items_fts` (FTS5) with an indexed `body` column and unindexed columns
       `id`, `item_type` (`assertion`/`entity`/`event`/`relationship`), `domain`, `context`,
       `epistemic_status`, `lifecycle_status`, `path_segments` (JSON-encoded list, empty for
       types other than `assertion` — the only type with a folder-path builder, TASK-014).
       `context` is the first-class field ADI-016 puts on all four canonical types (`NULL` when
       the item has none) — see "Relation to ADI-016/TASK-014a" below.
     - `build_index(vault_root, index_dir) -> None` — drops and recreates the SQLite file at
       `index_dir` from scratch via a full `scanner.py` walk of every domain. Idempotent,
       jettable at any time (INV-011).
     - `index_item(index_dir, item)` / `remove_item(index_dir, item_id)` — single-row upsert/
       delete, defined for future incremental use but not called by any pipeline in this ticket
       (see V1 scope decisions).
   - `search.py` — `search(index_dir, domain, query, item_type=None, context=None, limit=50,
     offset=0) -> (results, total)`: FTS5 `MATCH` against `body`, filtered by `domain` (required),
     `item_type` (optional) and `context` (optional), ordered by FTS5 `rank`, sliced by
     `limit`/`offset`. Each result
     includes an FTS5 `snippet()` excerpt around the match plus the item's full `body` (see
     rationale below) and its metadata columns.
2. New endpoint `GET /domains/<domain>/search` in a new `src/app/api/routes_search.py`:
   - Query params: `q` (required, non-empty string), `item_type` (optional, one of
     `assertion`/`entity`/`event`/`relationship`), `context` (optional, a single non-empty
     string — restricts results to items carrying that ADI-016 `context`), `limit`/`offset`
     (TASK-007a's `parse_pagination_args`, same defaults/bounds as every other list endpoint).
   - Response: `{"items": [...], "total": N, "limit": L, "offset": O}` (TASK-007a's envelope,
     reused via `serialization.paginate`/a shared per-item serializer). Each item:
     `{"id", "item_type", "domain", "context", "epistemic_status", "lifecycle_status",
     "path_segments", "snippet", "body"}`.
   - Full `body` is included in every result, not only the `snippet` — deliberate: TASK-019 has
     no separate canonical-item-detail endpoint to fetch from (none exists yet, see TASK-019's own
     Objective), so the search response itself must carry everything the frontend needs to expand
     a result inline. Matches this project's established "personal-scale, no premature
     optimization for volumes that don't exist yet" reasoning (e.g. TASK-007a's cursor-pagination
     rejection).
   - `q` missing or empty → `400` with `{"error": {"type": "ValidationError", "message": ...}}`
     (same `api.errors.ValidationError` class TASK-007a already introduced), before any index
     query runs.
   - `item_type` outside the four valid values → `400 ValidationError`, same pattern.
3. `src/app/api/app.py`: calls `retrieval.index_store.build_index(vault_root, config.retrieval.
   index_dir)` once during `create_app()`, before the app starts accepting requests — the index is
   always freshly rebuilt from the canonical files at process startup (see V1 scope decisions).
   Registers the new `search_bp` blueprint alongside the four existing ones.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **No in-memory-first staging step.** ADI-002's "Concrete scaling path" describes step 1
  (in-memory, rebuilt at startup) before step 2 (SQLite/FTS5). This ticket implements step 2's
  storage directly. Rationale (Cleo, 2026-09-06): building and testing a throwaway in-memory
  implementation only to replace it immediately is wasted work — going straight to the
  already-decided destination avoids maintaining two code paths for one ticket. ADI-002's actual
  architectural decision (derived, reconstructible, local, never-in-vault) is unchanged. Not
  treated as an ADI-002 amendment (no new ADR) because the destination itself doesn't change —
  same "flag in the ticket, don't reopen the ADR" precedent TASK-007a already set when it changed
  TASK-007's response shape. **But see the Objective's three-point deviation list**: skipping the
  staging step is only one of the three ways this ticket differs from ADI-002 as written.
- **The index is stale between restarts, and that is user-visible.** Since the only refresh is the
  full rebuild in `create_app()`, an item accepted during a running session (`accept_proposal`
  writes a new canonical file) is **not findable in search until the API process is restarted**.
  This is not a performance footnote — it is the search screen (TASK-019) silently failing to show
  something the reviewer just created, minutes earlier. Named here rather than discovered in use.
  ADI-002 anticipated exactly this ("if Cleo searches from a device she hasn't used in a while, its
  index may be stale until Pekopeko rebuilds… e.g. rebuild-on-launch if the vault's changed",
  Consequences) and left it to a later phase; nobody has owned it since. **Flagged for Cleo's
  decision at read time**: accept the restart-to-refresh limitation for V1, or pull one of
  (a) calling `index_item` from `review/pipeline.py`'s accept path, (b) a `POST .../search/rebuild`
  route, (c) a cheap mtime-based staleness check per request — into this ticket's scope. This
  ticket as written assumes (a)/(b)/(c) are all out.
- **Indexes only the four canonical item types, live versions only** — `proposals/` (review queue,
  not yet canonical), `sources/` (raw ingested content, not itself "knowledge") and every
  per-item `history/` subfolder (superseded snapshots, ADI-001) are explicitly excluded. Flagged
  for Cleo's confirmation at review time: if raw source content search turns out to be wanted too,
  that's an easy additive extension to `scanner.py`, not a redesign. Searching *historical* item
  states is a different question entirely and belongs to UC-015's own (still un-ticketed) scope,
  not here.
- **`context` is indexed and filterable, not derived here.** This ticket reads whatever `context`
  ADI-016/TASK-014a put in a canonical item's frontmatter and exposes it as a column plus an
  optional filter. It never computes, guesses, or defaults one (that is TASK-014b's scope), and it
  works unchanged against a vault where no item has a `context` yet — every row simply carries
  `NULL` and the filter is never used. See "Relation to ADI-016/TASK-014a" below.
- **No semantic/embedding search** — ADI-002 step 3, explicitly future work.
- **No relationship-based traversal in results** — depends on TASK-020's adjacency structure,
  not yet built.
- **Full rebuild at API startup, not incremental indexing wired into `review`/`ingestion`.**
  `index_item`/`remove_item` exist in `index_store.py` for a future ticket to call from
  `review/pipeline.py`'s accept/edit/reject paths, but this ticket does not modify any
  `completed` pipeline code to call them. A full rebuild at process startup is simpler, correct
  by construction, and judged acceptable at the project's current (personal-scale) item volume —
  revisit if rebuild time becomes noticeable, mirroring ADI-002's own "if the scan becomes
  costly" framing, just applied to the rebuild step instead of a live query-time scan.
- **Search is always scoped to exactly one domain**, required, never inferred — no cross-domain
  aggregate search. Consistent with INV-008/INV-009 and every existing endpoint; cross-domain
  operations remain a separate future concern (TASK-028/TASK-031 territory), not reopened here.
- **Full `body` returned per result, not only a snippet** — see Scope §2 rationale above.

### Relation to ADI-016/TASK-014a (added 2026-09-07, consistency review)

This ticket and TASK-019 were originally written the same day as TASK-014a/TASK-014b and cited
neither ADI-016 nor `context` anywhere — an omission with a concrete consequence, since TASK-019 is
by its own Objective **the first screen in the product where Cleo sees canonical knowledge at all**
after it leaves the review queue. Without a `context` column and filter, that screen mixes two
fictional universes with no way to separate them: exactly the symptom UC-018 ("Fictional Universe
Isolation" — two novels, two characters named "Alex") describes and that ADI-016 exists to fix.
Domain-level filtering does not help, because both novels live in the same `FICTION` domain.

Concretely: `context`'s physical position in the path (`<domain>/<type-plural>/<context>/…`,
ADI-016) means the scanner already walks past it; reading it from frontmatter and carrying it into
the index is additive and cheap. Ordering constraint, not a blocking dependency: if TASK-014a has
not landed when this ticket is implemented, no canonical file carries a `context` key yet — the
scanner reads `None` for every item, the column is uniformly `NULL`, the filter matches nothing,
and every other acceptance criterion here still holds. Nothing about this ticket needs to wait.

## Requirements

- Python only (ADI-007). `sqlite3` (stdlib) with FTS5 — no new entry in `src/requirements.txt`.
- Directory creation for `index_dir` and all SQLite file I/O live entirely in
  `src/app/retrieval/index_store.py` — no other module touches the index file directly.
- `build_index` must be safe to call against an `index_dir` that doesn't exist yet (creates it)
  and against one that already holds a previous index file (drops and recreates cleanly).
- Sorting/slicing for the paginated response follows TASK-007a's existing
  `parse_pagination_args`/`paginate` contract exactly — no divergent pagination shape.

## Constraints

- No git usage (project-wide constraint).
- The index file is never written inside the vault (`vault_root`) — always under
  `config.retrieval.index_dir`, which itself defaults outside the project/vault tree.
- No new HTTP surface beyond the single `GET /domains/<domain>/search` route — no index
  management endpoints (rebuild-on-demand, index stats) in this ticket.
- No modification to `review/`, `ingestion/`, `extraction/`, or `config/`'s existing public
  contracts — read-only consumers only.
- No cross-domain search (INV-008/INV-009).

## Files/modules concerned

- **New**: `src/app/retrieval/__init__.py`.
- **New**: `src/app/retrieval/scanner.py` — read-only frontmatter+body parsing for the four
  canonical item types, independent of `review.frontmatter`.
- **New**: `src/app/retrieval/index_store.py` — SQLite/FTS5 schema, `build_index`, `index_item`,
  `remove_item`.
- **New**: `src/app/retrieval/search.py` — `search()`.
- **New**: `src/app/api/routes_search.py` — the `GET /domains/<domain>/search` blueprint.
- **Modified**: `src/app/api/app.py` — registers `search_bp`; calls `build_index` once during
  `create_app()`.
- **New tests**: `src/tests/retrieval/test_scanner.py`, `test_index_store.py`, `test_search.py`;
  `src/tests/api/test_search_routes.py` (Flask `app.test_client()`, following
  `test_pagination.py`'s existing pattern).

## Dependencies

Read-only consumer of the on-disk file contracts already established by TASK-001/002/003/005/006/
013/014 (all `completed`) — no code import from any of them, no modification to their code.
Depends on TASK-007/TASK-007a (`completed`) for the API conventions (`app.py` blueprint
registration, `X-API-Key`, error envelope, `api.errors.ValidationError`,
`parse_pagination_args`/`paginate`) this ticket's route reuses. Independent of TASK-015/016/017.
**Soft-coupled to TASK-014a** (`backlog`, ADI-016's `context` field): not a blocking dependency —
see "Relation to ADI-016/TASK-014a" above for why this ticket works either way, and what is
degraded while TASK-014a is unimplemented.

## Acceptance criteria

1. `build_index` run against a fixture vault with assertions/entities/events/relationships across
   two domains produces a SQLite file whose `items_fts` table contains exactly those items (count
   and `id`s match), and none from `proposals/`, `sources/` or any `history/` subfolder even when
   all three exist in the fixture.
2. `search(index_dir, domain="PERSONAL", query=...)` never returns an item whose `domain` column
   is not `PERSONAL`, even when matching items exist in other domains in the same index.
3. `item_type="entity"` returns every matching entity and no assertion/event/relationship, even
   when their bodies also match the query text.
4. `GET /domains/<domain>/search?q=<term>` returns `200` with the `{items, total, limit, offset}`
   envelope; each item includes `snippet`, `body`, and all metadata columns from Scope §2.
5. `GET .../search` with `q` omitted or empty returns `400` with
   `error.type == "ValidationError"`, before any SQLite query runs.
6. `GET .../search?item_type=bogus` returns `400 ValidationError`.
7. Deleting the SQLite index file and calling `build_index` again reproduces an identical
   `items_fts` content from the same fixture vault — no data loss, confirming the index is purely
   derived (INV-011).
8. `limit`/`offset` behave identically to TASK-007a's existing list endpoints (same defaults,
   same bounds, same `400` on invalid values) — reusing `parse_pagination_args` directly.
9. `X-API-Key` missing/wrong on `GET .../search` returns `401`, before any index query runs — same
   as every other route (regression against TASK-007's existing auth behavior).
10. The app still binds `127.0.0.1` only and returns the standard CORS header on `GET .../search`
    — regression against TASK-007's existing app-wide behavior.
11. Starting the API (`create_app()`) against a fixture vault populates the index before the first
    request is served — a `GET .../search` immediately after startup (no prior explicit
    `build_index` call by the test) returns results from files already on disk at startup time.
12. A fixture item that has a `history/<timestamp>--v<n>.md` snapshot (`lifecycle_status:
    SUPERSEDED`, a *different* body from the live file) appears **exactly once** in
    `items_fts`, with the live body — searching for a term present only in the superseded body
    returns no result. Guards the `history/` exclusion directly rather than relying on the glob's
    shape (see Scope §1).
13. An item whose frontmatter carries `context: "tatouages"` is indexed with that value in its
    `context` column; `search(..., context="tatouages")` returns it and excludes an otherwise
    matching item from the same domain whose `context` is a different value or absent.
    `GET .../search?context=tatouages` behaves identically through the route.
14. Against a fixture vault where **no** item carries a `context` key (i.e. TASK-014a not yet
    implemented), `build_index` succeeds, every row's `context` is `NULL`, and AC1-AC11 all still
    hold — confirms the soft coupling stated in "Relation to ADI-016/TASK-014a".

## Testing requirements

`pytest`, `tmp_path` for both `vault_root` and `index_dir`, Flask's `app.test_client()` for route
tests, fixture vaults built directly via `review.storage`'s own
`write_assertion_file`/`write_entity_file`/`write_event_file`/`write_relationship_file` (so
fixtures match the real on-disk contract rather than a hand-rolled approximation), plus
`review.pipeline.edit_proposal` (or a hand-written snapshot matching TASK-006's `history/`
contract) for AC12's superseded-version fixture. Minimum: one test per acceptance criterion above
(14 total). Coverage ≥80% on `src/app/retrieval/` and
`src/app/api/routes_search.py`.

## Out of scope

- Incremental index updates wired into `review/pipeline.py` / `ingestion/pipeline.py` — a full
  rebuild at API startup is this ticket's V1 mechanism, with the staleness consequence named
  explicitly in V1 scope decisions rather than left for Cleo to discover in use.
- Searching superseded/historical item versions (`history/`) — UC-015's own concern, un-ticketed.
- Deriving or defaulting a `context` value (TASK-014b) — this ticket only reads and filters it.
- Semantic/embedding-based search (ADI-002 step 3).
- Relationship-based result traversal (depends on TASK-020, not yet built).
- Cross-domain search.
- Index management endpoints (manual rebuild trigger, index stats/health).
- Any frontend code — TASK-019.
