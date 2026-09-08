# TASK-014b: Context Derivation — Source Folder, with LLM Fallback (Both Pipelines)

- **Status**: completed

## Objective

Populate the `context` field TASK-014a introduces, per ADI-016. Primary signal: the ingested
file's own source-folder location (e.g. a file found at `.../PERSONAL/_inbox/sport/suivi
calories.md` gets `context: "sport"`) — this is the mechanism Cleo originally asked for. Fallback,
when no folder signal exists: a single lightweight one-shot LLM call per note, guessing whether the
note belongs to a distinct project/universe, degrading to `context: None` (never a forced
non-empty value — see ADI-016) when the model is unsure.

Applies symmetrically to **both** pipelines — `ingestion/` (assertions) and `extraction/`
(entity/event/relationship) — since ADI-016 made `context` cross-type. Each pipeline gets its own,
independent implementation (no shared import between `ingestion/` and `extraction/`), matching the
module-independence discipline TASK-002 established and `scan_existing_assertion_folders`
(ADI-014) already follows for its own reimplementation.

**Blocking dependencies**: TASK-014a (needs the `context` field/parameters to exist before there is
anywhere to put a derived value) and **TASK-001f** (needs `scan_once`'s recursive inbox-scanning,
added by this ticket, to discover a nested source file like `_inbox/sport/file.md` at all — today's
TASK-001f design only lists direct children of `_inbox/`). This is the ticket that actually
"depends on TASK-001f," per Cleo's original framing.

## Binding context (references, not duplicated here)

- **ADI-016** (Accepted): the decision this ticket populates — read it in full, especially "genuinely
  optional, no forced fallback" and "once per source note, not per item," both binding constraints
  on this ticket's mechanism.
- **TASK-014a** (this ticket's blocking prerequisite): the `context` parameters on
  `assertion_path`/`entity_path`/`event_path`/`relationship_path`/`write_*_file`/`accept_proposal`
  this ticket's derived value flows into.
- **TASK-001f** (`specs/tasks/backlog/TASK-001f-automatic-folder-ingestion.md`, `backlog`, blocking):
  `scan_once`'s Scope item 3 currently lists only **direct children** of
  `<vault_root>/<domain>/_inbox/`. This ticket amends that design (before or as part of TASK-001f's
  own implementation, whichever lands first — same "amend an unimplemented sibling ticket's
  intended behavior via a satellite" posture already used throughout this project) to recurse into
  subfolders, preserving each file's full nested `source_path` unchanged through to `ingest_source`
  (no signature impact — `ingest_source` already accepts any `Path`).
  **Second, independent amendment to TASK-001f (2026-09-07, consistency review)**: that ticket now
  moves each file into `<inbox_dirname>/<processed_dirname>/` **before** dispatching, and passes
  the post-move path to `ingest_source` — the original dispatch-then-move ordering handed the
  background thread a path that no longer existed. See TASK-001f's own "Move-before-dispatch"
  section. Consequence here: the `source_path` this ticket's `_derive_source_context` receives from
  the watcher path is `…/_inbox/<processed_dirname>/<context>/file.md`, not
  `…/_inbox/<context>/file.md`. Both shapes must be handled (Scope §3, AC15) — which is why
  `processed_dirname` is in the context dict at all.
- `src/app/ingestion/pipeline.py:36` (`ingest_source`), context dict built at `:145`
  (`provider.extract(content, {"source_path": ..., "vault_root": ..., "domain": ...})`) — the exact
  point ADI-014 already used to add `vault_root`/`domain` additively; this ticket adds
  `inbox_dirname`/`processed_dirname` the same way.
- `src/app/extraction/pipeline.py:49` (`extract_source`) — structurally identical to
  `ingest_source`; its own `provider.extract()` context-dict construction point gets the same two
  new keys.
- `src/app/ingestion/providers/base.py` (`ExtractedAssertion`) and
  `src/app/extraction/providers/base.py` (`ExtractedEntity`, `ExtractedEvent`,
  `ExtractedRelationship`) — the four dataclasses gaining `context: Optional[str] = None`.
- `src/app/ingestion/providers/ollama_provider.py:217-247` (`_ensure_path_segments`) and
  `:20-21,274` (`PATH_PROPOSAL_MAX_ATTEMPTS`, `FALLBACK_PATH_SEGMENTS`, `_normalize_path_string`) —
  the existing per-assertion taxonomy machinery this ticket's `context` derivation sits alongside
  (not inside — different granularity, see Objective) and reuses `_normalize_path_string` for
  folder-name cleanup rather than reinventing it.
- `src/app/extraction/providers/ollama_provider.py` — the `extraction/`-side provider getting its
  own independent, parallel implementation (no import from `ingestion/`).
- `src/app/config/schema.py::FolderWatchConfig` (`inbox_dirname`, `processed_dirname` — added by
  TASK-001f) — the source of the two new context-dict keys.

## Scope

### Shared mechanism (implemented independently in each pipeline's own provider)

1. `ingestion/pipeline.py::ingest_source` and `extraction/pipeline.py::extract_source`: each
   `context` dict passed to `provider.extract()` gains `inbox_dirname`/`processed_dirname`, read
   from `load_config().folder_watch` — additive, mirrors exactly how ADI-014 already added
   `vault_root`/`domain`. No change to either function's public signature.
2. `ExtractedAssertion` (`ingestion/providers/base.py`) gains `context: Optional[str] = None`
   (distinct field from its existing `proposed_path_segments`). `ExtractedEntity`, `ExtractedEvent`,
   `ExtractedRelationship` (`extraction/providers/base.py`) each gain the same new field (none of
   them carry any path-related field today).
3. `ingestion/providers/ollama_provider.py::_derive_source_context(context: dict) -> Optional[str]`
   (new): reads `source_path`, `vault_root`, `domain`, `inbox_dirname`, `processed_dirname` from
   `context`. If `source_path` resolves under `<vault_root>/<domain>/<inbox_dirname>/<subfolder>/...`
   — **or under `<vault_root>/<domain>/<inbox_dirname>/<processed_dirname>/<subfolder>/...`, with
   the `processed_dirname` segment skipped** — returns the first subfolder name,
   normalized via the existing `_normalize_path_string` (reused, not reinvented — same
   accent-stripping/lowercasing/HTML-unescaping applied to taxonomy segments, for naming
   consistency). Returns `None` if `source_path` sits directly in `<inbox_dirname>/` with no
   subfolder, if it's outside the inbox tree entirely (e.g. a manually-triggered ingestion of an
   arbitrary path), or if any required context key is missing — safe degrade, never raises
   (INV-019).
4. `extraction/providers/ollama_provider.py::_derive_source_context` — independent reimplementation
   of #3 (same logic, no shared import, consistent with `scan_existing_assertion_folders`'s own
   precedent for `ingestion`/`extraction` independence).
5. `extract()` in both providers calls its own `_derive_source_context` **once per call** (per
   source note), before/alongside its existing per-item extraction logic. If it returns a value,
   every assertion/entity/event/relationship produced by that call gets `context` set to it — no
   further LLM call needed for context on that note.
6. **LLM fallback, once per note, only when `_derive_source_context` returns `None`**: a single
   dedicated Ollama call (assertion text is *not* needed here, unlike `_propose_path` — this is a
   note-level question, not a per-item one) asking whether the note's content suggests it belongs
   to a specific ongoing project/universe distinct from general domain content, given the note's
   full text. Retried the same way `_propose_path_with_retry` retries (reusing the existing
   attempt-count constant, `PATH_PROPOSAL_MAX_ATTEMPTS`), but **on exhausting retries, or on any
   ambiguous/empty response, the result is `None` — not a forced fallback string** (deliberate
   contrast with `FALLBACK_PATH_SEGMENTS`, unrelated and unchanged). The resolved value (`str` or
   `None`) is applied to every item the call produces, same as the folder-derived case.
7. `src/app/ingestion/watcher.py` (new module per TASK-001f's own Scope item 3; extended here, not
   rewritten): `scan_once` walks `<vault_root>/<domain>/<inbox_dirname>/` **recursively** instead of
   listing only direct children — still skipping dotfiles/dot-directories and the entire
   `<processed_dirname>/` subtree at any depth, still dispatching `ingest_source` with each file's
   full nested path unchanged. On move-to-processed, mirrors the file's relative subfolder path
   under `<processed_dirname>/...` (creating intermediate directories as needed) instead of
   flattening to `<processed_dirname>/<filename>` — this is what makes the discovered
   `source_path` still carry the subfolder information `_derive_source_context` (#3) needs, and
   avoids collisions between same-named files from different context folders.

### V1 scope decisions (explicit — flag disagreement, don't silently deviate)

- **Only the first subfolder level under `<inbox_dirname>/` becomes `context`.** A file at
  `_inbox/sport/nutrition/file.md` gets `context: "sport"`; `"nutrition"` is not captured anywhere
  by this ticket (it is not fed into `proposed_path_segments` either — that stays the existing
  per-assertion LLM taxonomy proposal's own job, unaffected by this ticket, and only exists for
  assertions in the first place). Matches Cleo's own examples, which are all exactly one level
  deep. If deeper nesting needs to become taxonomy segments too, that is separate future work, not
  silently expanded into here.
- **No coordination between `ingestion/`'s and `extraction/`'s LLM-fallback guesses for the same
  note.** The folder-derived case is deterministic and will always agree between the two pipelines
  for the same file; the LLM-guess fallback could in principle diverge between them (see ADI-016's
  own stated known limitation) — not fixed here, consistent with ADI-014/015's own precedent of
  naming a known limitation rather than silently ignoring or over-engineering around it in V1.
- **No prompt-quality tuning beyond a minimal, clear instruction** — same V1 posture TASK-001e
  itself took for its own first attempt (which then needed ADI-014/015 amendments once verified in
  production). If this ticket's fallback proves as unreliable as TASK-001e's original optional
  suffix did, that is a future amendment, not pre-empted speculatively here.
- **No OS-level filesystem watcher** — `scan_once`'s recursion is still polling-based, per ADI-013,
  unchanged.

## Requirements

Python only, no new dependency. Same testing discipline as TASK-001e/TASK-001f: `pytest`,
`tmp_path`, mocked/fake provider responses (no real Ollama call in the default test suite), no real
`time.sleep` in `scan_once` tests.

## Constraints

- No change to `ingest_source`'s or `extract_source`'s public signatures.
- No change to `ExtractedAssertion.text`/`.epistemic_status`/`.proposed_path_segments` or their
  existing validation/behavior — `context` is a wholly new, independent field alongside them.
- `context` is always `Optional[str]`, defaulting to `None`, never forced non-null (ADI-016) —
  this is a hard constraint distinguishing this ticket from TASK-001e/ADI-014's own mandatory-path
  precedent; do not copy that machinery's "always non-empty" guarantee here.
- No change to `FALLBACK_PATH_SEGMENTS`/`PATH_PROPOSAL_MAX_ATTEMPTS`'s existing meaning or use for
  taxonomy segments — this ticket's own retry count may reuse the same constant's *value* but must
  not repurpose or mutate the constant's existing taxonomy-segment semantics.
- A domain with no `_inbox/` folder yet, or a subfolder that disappears mid-scan, must not raise
  (INV-019) — same posture TASK-001f's own AC10 already established for the flat case.
- Recursion into `_inbox/` subfolders must not change TASK-001d's existing duplicate-detection
  behavior, which is content-hash-based and already path-agnostic (INV-020).

## Files/modules concerned

- `src/app/ingestion/pipeline.py` (`ingest_source`, context dict), `src/app/ingestion/providers/base.py`
  (`ExtractedAssertion`), `src/app/ingestion/providers/ollama_provider.py`
  (`_derive_source_context`, one-shot LLM fallback, integration into `extract()`).
- `src/app/extraction/pipeline.py` (`extract_source`, context dict), `src/app/extraction/providers/base.py`
  (`ExtractedEntity`, `ExtractedEvent`, `ExtractedRelationship`),
  `src/app/extraction/providers/ollama_provider.py` (independent `_derive_source_context` +
  fallback, mirroring the ingestion-side implementation without importing it).
- New: `src/app/ingestion/watcher.py` (`scan_once` recursion — implemented here if TASK-001f hasn't
  landed yet, or amended here if it has).
- New/updated tests in `src/tests/ingestion/` and `src/tests/extraction/` mirroring TASK-001e's own
  test structure: `_derive_source_context` unit tests (no subfolder → `None`; one level → the
  normalized name; path outside inbox tree → `None`; missing context keys → `None`, no raise);
  once-per-note application across a multi-item extraction result; LLM-fallback retry/degrade-to-
  `None` behavior; `scan_once` recursive discovery and `processed/` mirroring.

## Dependencies

TASK-014a (**blocking** — needs the `context` field/parameters to exist). TASK-001f (**blocking** —
needs recursive inbox scanning for the automatic-ingestion path to discover nested files at all;
the provider-level derivation logic is independently testable via direct `ingest_source`/
`extract_source`/`extract()` calls with a hand-built nested `source_path`, same posture TASK-014
used for citing TASK-013 as blocking only for one half of its own scope). ADI-016 (Accepted,
binding contract). TASK-001e/ADI-014/ADI-015 (`completed`/Accepted, cited for the machinery this
ticket sits alongside, not modified).

## Acceptance criteria

1. `_derive_source_context` (both pipelines' independent implementations) returns `None` for a
   `source_path` directly inside `<inbox_dirname>/` with no subfolder.
2. `_derive_source_context` returns the normalized first-subfolder name for a `source_path` one
   level deep (e.g. `_inbox/sport/file.md` → `"sport"`).
3. `_derive_source_context` returns `None` for a `source_path` outside
   `<vault_root>/<domain>/<inbox_dirname>/` entirely (e.g. a manually-triggered ingestion of an
   arbitrary path) — no raise.
4. `_derive_source_context` returns `None`, without raising, when `vault_root`/`domain`/
   `inbox_dirname`/`processed_dirname` is missing from `context`.
5. A dirty folder name (accents, HTML entities, mixed case) is normalized via the existing
   `_normalize_path_string` the same way a taxonomy segment would be.
6. When `_derive_source_context` returns a value, `extract()` applies it identically to every
   assertion/entity/event/relationship the call produces (multi-item batch test).
7. When `_derive_source_context` returns `None`, the LLM fallback is called exactly once per
   `extract()` call, not once per item.
8. The LLM fallback, on a clear/confident response, sets `context` to the model's answer for every
   item in the batch.
9. The LLM fallback, on an ambiguous/empty response or after exhausting retries, sets `context` to
   `None` for every item in the batch — never a forced non-empty value.
10. `ingest_source`'s and `extract_source`'s public signatures are unchanged (regression check by
    direct comparison, same as every prior satellite).
11. `scan_once` discovers a file nested one level under `_inbox/` (e.g. `_inbox/sport/file.md`),
    moves it to `_inbox/processed/sport/file.md` (mirrored, not flattened), and dispatches
    `ingest_source` with that post-move path — which exists on disk at dispatch time
    (TASK-001f AC5/AC7, move-before-dispatch ordering).
12. `scan_once` still correctly skips the entire `processed/` subtree at any depth and dotfiles/
    dot-directories, without regression to TASK-001f's own flat-case acceptance criteria.
13. An end-to-end call: ingesting a hand-placed file at `.../PERSONAL/_inbox/sport/file.md` via
    `ingest_source` directly produces Proposals whose `context` is `"sport"`; the same test run
    against `.../PERSONAL/_inbox/processed/sport/file.md` (the path the watcher actually dispatches
    with, per TASK-001f's move-before-dispatch ordering) produces the identical result.
14. Recursion into `_inbox/` subfolders does not change TASK-001d's existing duplicate-detection
    behavior (regression test against an existing TASK-001d test case, run against a nested path).
15. `_derive_source_context` returns the same value for the **post-move** path the watcher actually
    dispatches with (`_inbox/processed/sport/file.md` → `"sport"`) — the `processed_dirname`
    segment is skipped, not mistaken for the context. A file moved straight to
    `_inbox/processed/file.md` with no subfolder still returns `None` (AC1's rule, unchanged).
    Required by TASK-001f's move-before-dispatch ordering; see that ticket's own section.

## Testing requirements

`pytest`, `tmp_path`, mocked/fake providers (no real Ollama call in the default suite), no real
`time.sleep`, covering AC1-15. Project-wide bar: at least 80% coverage on every file touched.

## Out of scope

- Any OS-level filesystem watcher (`watchdog` or similar) — polling only, per ADI-013.
- Coordinating the two pipelines' independent LLM-fallback guesses for the same note (see V1 scope
  decisions).
- Capturing more than one subfolder level as `context` (see V1 scope decisions).
- Any change to `proposed_path_segments`'s own existing per-assertion machinery, `FALLBACK_PATH_SEGMENTS`,
  or `PATH_PROPOSAL_MAX_ATTEMPTS`'s taxonomy-segment semantics.
- Entity/relationship dedup-by-context (ADI-016, no mechanism exists to make context-aware).
- Any UI (Settings screen or otherwise) to toggle or configure inbox recursion — `config.yaml`
  only, matching TASK-001f's own posture.

## Verification record (2026-09-08)

Verified by Claude in the same session as implementation — same disclosed limitation as every prior
ticket in this project: not a second independent reviewer. Implemented together with TASK-014a at
Cleo's explicit request, out of the roadmap's strict order (TASK-015 remained the "official" next
action) — precedent already set by TASK-016/017/018/019.

**TASK-001f absorbed into this ticket's implementation, as this ticket's own text anticipated.** This
ticket's own "Files/modules concerned" said `src/app/ingestion/watcher.py` would be "implemented here
if TASK-001f hasn't landed yet, or amended here if it has." TASK-001f was still 100% unbuilt (no
`watcher.py` existed anywhere in the repo, confirmed by direct search before starting) when this
session began — confirmed explicitly with Cleo before proceeding (not assumed) that this session
should build TASK-001f's `FolderWatchConfig`/`scan_once`/`start_folder_watcher` machinery as part of
this ticket, correctly recursive from the start rather than built flat then amended, since TASK-001f
itself was never separately implemented. **TASK-001f's own file
(`specs/tasks/backlog/TASK-001f-automatic-folder-ingestion.md`) is moved to `completed/` alongside
this one, with a pointer back to this ticket** rather than getting its own separate implementation
session — its full scope (config schema/loader, `scan_once`, `start_folder_watcher`, `api/app.py`
wiring, all 13 of its own ACs) landed here, and its own AC set is folded into this ticket's own
AC11-15 plus the embedded acceptance criteria below.

Real gaps found during implementation, not anticipated by either ticket's text, fixed in the same
session:
- `scan_once`'s `rglob("*")` walk had to be materialized into a list before any move began — moving a
  file into `processed/` while still walking the same tree, and a subfolder disappearing mid-scan
  (the ticket's own stated constraint), both risk breaking the live iterator. Caught and fixed before
  landing, not discovered as a bug afterward.
- `scan_proposed_path_segments`' new `context` parameter needed an explicit `is not None` guard on the
  filter — an unconditional equality check would have silently broken the `context=None` "return
  everything" regression guarantee once real proposals started carrying non-null `context` values.
- `run_in_background` and the `VALID_DOMAINS` literal are duplicated locally in `watcher.py` rather
  than imported from `api/`, matching this codebase's own established "no module imports another
  module's internals for shared constants" convention (and avoiding inverting the `api/` → `ingestion/`
  dependency direction).
- `api/app.py::create_app`'s new eager `build_configured_provider(config)` call is itself gated on
  `config.folder_watch.enabled`, not left to `start_folder_watcher`'s own no-op check — otherwise a
  disabled watcher would still pay the cost (and risk, e.g. a missing `requests` install) of
  constructing a real provider at app-factory time for a feature that isn't even turned on.
- `ingestion/storage.py::write_proposal_file` and `extraction/storage.py`'s three
  `write_*_proposal_file` functions (plus the shared `_base_proposal_frontmatter` helper) needed an
  explicit `context` passthrough from the `Extracted*` dataclass into the written Proposal's own
  frontmatter — without it, `context` would be computed by the provider but never actually reach disk,
  breaking the whole chain `accept_proposal` (TASK-014a) depends on reading from.

- `[PASS]` `pytest src/tests/ingestion --cov=src/app/ingestion`: **139/139 pass**, `watcher.py` at 97%
  coverage (only a defensive, effectively-unreachable `except ValueError` branch on
  `entry.relative_to()` uncovered), every other touched file at 98-100%. Plus the same 2 pre-existing,
  unrelated failures every ticket since TASK-014 has documented, reconfirmed via `git stash`/re-run/
  `git stash pop`.
- `[PASS]` `pytest src/tests/extraction --cov=src/app/extraction`: **114/114 pass**, 100% coverage on
  every file in the package.
- `[PASS]` `pytest src/tests/config --cov=src/app/config`: **46/46 pass**, 100% coverage.
- `[PASS]` `pytest src/tests/api --cov=src/app/api`: **116/116 pass**, `app.py` at 94% (remaining gaps
  are pre-existing/untouched: the `OPTIONS` early-return branch and the never-exercised `main()`
  entrypoint — this ticket's own new code, the `folder_watch.enabled` branch, is fully covered).
- `[PASS]` `npx vitest run` + `npx vite build` (frontend, shared with TASK-014a): **113/113 pass**,
  build succeeds.
- `[PASS]` Manual end-to-end reproduction, actually executed (not narrated): a script placing a
  hand-built file at `<vault>/PERSONAL/_inbox/sport/suivi_calories.md`, calling `scan_once` directly
  with `folder_watch.enabled=True` and a fake (non-network) provider mimicking
  `OllamaProvider._derive_source_context`'s behavior. Confirmed: the file moves to
  `_inbox/processed/sport/suivi_calories.md`; the dispatched background `ingest_source` task completes;
  a Proposal is written with `context: "sport"` in its frontmatter; `accept_proposal` on that Proposal
  writes the canonical file to `PERSONAL/assertions/sport/activites/<id>/<id>.md` (context-segmented
  path, matching TASK-014a's own path placement) with `context: "sport"` in its own frontmatter and
  the correct body. No real Ollama call — consistent with this ticket's own Testing requirements
  (mocked/fake provider only).

Acceptance criteria checked one by one:

- `[PASS]` AC1 `_derive_source_context` (both pipelines) → `None` for a file directly in `_inbox/`.
- `[PASS]` AC2 → normalized first-subfolder name one level deep.
- `[PASS]` AC3 → `None` for a `source_path` outside the inbox tree entirely, no raise.
- `[PASS]` AC4 → `None`, no raise, when any required context key is missing.
- `[PASS]` AC5 dirty folder name normalized via the existing `_normalize_path_string`.
- `[PASS]` AC6 folder-derived context applied identically to every item in a multi-item batch.
- `[PASS]` AC7 LLM fallback called exactly once per `extract()` call, not once per item.
- `[PASS]` AC8 confident fallback response sets `context` for every item in the batch.
- `[PASS]` AC9 ambiguous/empty response or exhausted retries sets `context` to `None`, never forced
  non-empty.
- `[PASS]` AC10 `ingest_source`/`extract_source` public signatures unchanged (regression check).
- `[PASS]` AC11 `scan_once` discovers a file nested one level under `_inbox/`, moves it mirrored (not
  flattened) into `processed/`, dispatches with the post-move path that exists on disk at dispatch time.
- `[PASS]` AC12 `scan_once` still skips the entire `processed/` subtree at any depth and
  dotfiles/dot-directories.
- `[PASS]` AC13 end-to-end: both `_inbox/sport/file.md` and `_inbox/processed/sport/file.md` produce
  identical `context: "sport"` results (verified directly via `_derive_source_context` unit tests and
  the manual end-to-end script above).
- `[PASS]` AC14 recursion into `_inbox/` subfolders doesn't change TASK-001d's duplicate-detection
  behavior — regression test against a nested `source_path`, content-hash-based skip still fires.
- `[PASS]` AC15 `_derive_source_context` skips the `processed_dirname` segment, not mistaking it for
  the context; a file moved straight to `_inbox/processed/file.md` with no subfolder still returns
  `None`.

Embedded TASK-001f acceptance criteria (absorbed into this ticket, see note above):

- `[PASS]` `FolderWatchConfig` defaults load correctly when the section is absent from `config.yaml`.
- `[PASS]` An explicit `folder_watch` section overrides any subset of its 4 fields, omitted fields keep
  defaults.
- `[PASS]` An invalid `poll_interval_seconds` (non-positive, non-integer) raises `ConfigError`, same as
  empty `inbox_dirname`/`processed_dirname`.
- `[PASS]` `enabled=False` → `start_folder_watcher` starts no thread, no observable side effect
  (verified both directly and via `create_app()`, which now gates provider construction on `enabled`
  too).
- `[PASS]` `scan_once` dispatches a stable file with the post-move path, which exists on disk at
  dispatch time.
- `[PASS]` `scan_once` does not dispatch a file whose mtime is too recent.
- `[PASS]` After a successful dispatch, the file is present in `processed/` (mirrored) and absent from
  `_inbox/`.
- `[PASS]` A name collision in `processed/` is resolved by suffixing, never overwriting.
- `[PASS]` Dotfiles/dot-directories and the `processed_dirname` subfolder itself are never dispatched.
- `[PASS]` A domain with no `_inbox/` yet does not raise — created (with `processed/`) on first tick,
  contributes no dispatches.
- `[PASS]` `scan_once` returns the dispatched `task_id`s for direct test assertion.
- `[PASS]` `ingest_source`'s public signature is unchanged (regression check, shared with AC10 above).
- `[PASS]` A failing move (patched `shutil.move`) dispatches nothing for that file, no task state
  created; the tick completes and other files in the same `_inbox/` are still processed.
