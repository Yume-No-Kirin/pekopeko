# ADI-014: Mandatory Extraction-Proposed Folder Path (amends ADI-012)

- **ID**: ADI-014
- **Date**: 2026-09-04
- **Status**: Accepted (confirmed by Cleo on 2026-09-04, while verifying TASK-001e in production)

## Context

ADI-012 decided the folder path shown to a reviewer before any edit "is proposed by the
extraction LLM at ingestion/extraction time, not left empty by default" but "must degrade to an
empty list cleanly wherever the provider doesn't supply one" — TASK-001e implemented exactly
that: an optional `| <segment1>/<segment2>/...` suffix appended to the existing
`<epistemic_status>: <assertion_text>` line format, degrading to `proposed_path_segments: []`
whenever a response line omitted it.

Verifying TASK-001e in production (re-ingesting the real vault note `Plot Tatouages.md` against
`qwen2.5:7b`) showed the degrade path firing 100% of the time, not occasionally: the raw Ollama
response was inspected directly (not just the parsed output, ruling out a parsing bug) across two
separate real runs — 0 of 39 lines, then 0 of 79 lines, ever carried the suffix. Root cause,
confirmed by re-reading the actual prompt sent: the instruction was explicitly optional ("omit the
suffix entirely if you have no proposal"), positioned as the 6th of 6 instructions, and only 1 of
4 example lines demonstrated it — an easy pattern for a 7B instruction-following model to ignore
in favor of the majority (no-suffix) form it saw more of.

Cleo's response: every proposal must have a dedicated path — not something the model can silently
decline to propose.

## Decision

**`OllamaProvider.extract()` now guarantees a non-empty `proposed_path_segments` for every
assertion it returns.** This amends ADI-012's "degrades to an empty list" clause for this
provider specifically — the general `Provider` contract is unchanged (see Consequences).

Mechanism, each point confirmed explicitly by Cleo:

1. **Granularity: per-assertion, not per-note.** A note's assertions can end up in different
   folders. Chosen over a single call per note (cheaper, one path shared by every assertion from
   that note) specifically to allow this — accepted as worth the extra Ollama calls.
2. **The existing TASK-001e inline suffix stays as a first, cheap attempt** (unchanged mechanism).
   Only assertions it left empty trigger anything further.
3. **A dedicated second call per remaining assertion**, given: the assertion's own text, the full
   source note's content (so the model sees the assertion in its original context, not in
   isolation), and the list of folder paths already used under `<domain>/assertions/` in the vault
   (new `scan_existing_assertion_folders`, an independent reimplementation of
   `review/storage.py`'s `scan_organization_folders` returning full `"/"`-joined paths instead of
   depth-grouped segment names — same module-independence discipline TASK-002 established between
   `review/` and `ingestion/`).
4. **Retry then fallback, not a hard failure.** Up to `PATH_PROPOSAL_MAX_ATTEMPTS` (3) attempts;
   both an empty/malformed response and a network/HTTP error count as a failed attempt and are
   retried silently. If all attempts fail, a fixed `["uncategorized"]` segment is used instead of
   raising. Cleo explicitly chose this over hard-failing the ingestion task (the ADI-011
   zero-output precedent, rejected for this specific case) and over the empty-list degrade ADI-012
   originally specified.

## Alternatives considered

- **One second call per note (shared path for all its assertions).** Cheaper (1 extra call
  instead of up to N), but rejected: prevents assertions from the same note landing in distinct,
  thematically-appropriate folders, which is exactly what "per-assertion" is for.
- **Hard-fail the ingestion task if the second call can't produce a path**, consistent with
  ADI-011's zero-output precedent. Rejected: one stubborn assertion would block an entire note's
  ingestion; retry-then-fallback keeps progress unblocked while still giving every proposal a real
  (if sometimes generic) dedicated path.
- **No existing-folder context.** Simpler, but rejected: without it the model has nothing to
  anchor naming on, compounding the naming-drift problem noted below.

## Consequences

- `proposed_path_segments` is, in practice for the OllamaProvider path, always a real path — never
  `[]`, though it may be the literal fallback `["uncategorized"]`.
- This is an **OllamaProvider-specific guarantee, not a `Provider`-protocol-wide one**:
  `ExtractedAssertion.proposed_path_segments` keeps its `[]` default at the dataclass level
  (TASK-001e, unchanged), and a different/future `Provider` implementation remains free to return
  `[]` per ADI-012's original wording — only `OllamaProvider` now guarantees non-empty.
- **Cost**: up to N+1 Ollama calls per ingested note instead of 1 (N = assertion count). Verified
  in production: ~85 assertions from one note added roughly +25s beyond the ~50s extraction call
  (~75s total for 80 proposals) — Ollama's prompt-prefix caching on the "full note content" block
  shared across all of a note's path-proposal calls keeps the per-call marginal cost low after the
  first.
- **Known limitation, observed and not fixed by this ADR**: `scan_existing_assertion_folders` only
  sees *accepted* (canonical) assertions. A domain with nothing accepted yet gives the model no
  existing-folder anchor, so independent calls for near-duplicate themes from the same note can
  each invent a different naming convention — observed directly in the verification run
  (`système/tatouages`, `systeme_des_tatouages/tatouages`, `système-des-tatouages/tatouages`: three
  spellings of one real theme, none reused from another call). Expected to self-correct as more
  assertions get accepted into canonical folders over time (each subsequent ingestion sees a
  growing, real existing-folder list); no code addresses it now.
- No change to `ingest_source`'s public signature — `pipeline.py` only adds two keys
  (`vault_root`, `domain`) to the `context` dict already passed to `Provider.extract()`, additive
  to the existing `Provider` protocol.
- **Supersedes TASK-001e's AC4 and AC5 as originally written** (a missing/empty `|` suffix
  producing `proposed_path_segments: []`) — those two acceptance criteria described TASK-001e's
  original, now-amended behavior. The corresponding tests were rewritten in place to assert the
  new mandatory path-proposal-call behavior instead; see TASK-001e's own ticket for the amendment
  note and updated test list.
