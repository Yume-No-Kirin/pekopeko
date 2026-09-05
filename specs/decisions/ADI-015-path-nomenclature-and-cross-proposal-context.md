# ADI-015: Path-Segment Nomenclature Enforcement + Cross-Proposal Context (amends ADI-014)

- **ID**: ADI-015
- **Date**: 2026-09-04
- **Status**: Accepted (confirmed by Cleo on 2026-09-04, from a real screenshot of the
  ADI-014 verification run)

## Context

ADI-014 made the extraction-proposed folder path mandatory, but did not constrain its content —
whatever the model returned was normalized only by trimming and splitting on `/`. A real
screenshot of that verification run showed the model's raw output was messy in several
recognizable ways: HTML entities leaking through (`&amp;`), accented French left as-is, two
concepts glued into one segment (`enjeux&themes`, `coopération_vs_pouvoir_solitaire`,
`symbiose-vs-domination`), multi-word segments joined by `_`/`-` instead of split into their own
folder levels, and singular/plural drift for the same concept. This is the same failure mode
ADI-014 itself was created to fix (relying on prompt instructions alone is not enough for a 7B
model) — it had simply moved from "does it propose a path at all" to "is the path clean."

Cleo also asked for the existing-folder context ADI-014 introduced to go further: include paths
already proposed by other, not-yet-accepted Proposals (not just the canonical accepted tree), and
paths already chosen earlier in the *same* extraction batch — so a note's own assertions, and
later notes, stop inventing a new spelling for what is really the same folder.

## Decision

**Nomenclature enforcement is now mandatory and deterministic, not prompt-dependent.** Every raw
path string - from either the cheap inline suffix or the dedicated second call - is run through a
new `_normalize_path_string` (`ollama_provider.py`) before being accepted as
`proposed_path_segments`:

1. HTML-unescape the raw string.
2. Split on `/` (existing top-level segment boundary).
3. Within each part, treat `&` and any run of whitespace/`_`/`-` as a token boundary — this is
   what turns one bad segment into several clean ones and is why splitting happens *before*
   connector-word filtering (a `\b`-anchored regex on the raw string would miss `vs` inside
   `cooperation_vs_pouvoir`, since `_` counts as a word character and blocks the boundary).
4. Per token: strip accents (`unicodedata` NFKD, plus explicit `œ`/`æ` handling since NFKD
   doesn't decompose those), lowercase, strip any remaining non-`[a-z0-9]` character.
5. Drop empty tokens and a small connector/stopword set (`vs`, `et`, `and`, plus the bare
   `de`/`du`/`des`/`la`/`le`/`les`/`l` grammatical glue words — conservative, not general French
   stopwords).

The prompt (both `_build_extraction_prompt`'s item 6 and `_build_path_prompt`) is also updated
with explicit nomenclature rules and a worked example (`mission/intrigue_academie/conflict
Escalation` → `intrigue/mission/conflit/escalation`) to reduce how often the normalizer has to do
real work — but the normalizer is the actual guarantee, the prompt is only there to help.
Semantic judgment the normalizer can't do mechanically (dropping a redundant word, translating,
reordering by specificity) is left to the model; the normalizer only guarantees clean formatting.

**Existing-folder context is now the union of three sources**, accumulated in `existing_folders`
by `_ensure_path_segments`:

1. `scan_existing_assertion_folders` (unchanged, ADI-014): canonical, accepted assertions.
2. New `scan_proposed_path_segments` (`storage.py`): paths already proposed by Proposals with
   `proposal_status` `PROPOSED` or `EDITED` (i.e. "processed but not yet accepted", Cleo's own
   wording) elsewhere in the domain, read from each Proposal file's frontmatter.
3. **In-batch accumulation**: as `_ensure_path_segments` resolves each assertion in the current
   `extract()` call, its normalized path is appended to the same in-memory `existing_folders`
   list before the next assertion is resolved — so assertion #40 of a note can see the path
   assertion #12 of the *same* note just chose, before anything is written to disk.

## Alternatives considered

- **Rely only on better prompt wording**, no server-side normalizer. Rejected: this is exactly
  the mistake ADI-014 was created to correct for the "propose a path at all" problem: a 7B model
  does not reliably follow formatting instructions, so the same class of failure would just
  resurface for formatting instead of presence.
- **Attempt semantic deduplication/translation/reordering in the normalizer** (e.g. picking one
  side of a "X vs Y" segment instead of splitting both into their own folders, or translating
  stray English words to French). Rejected as unreliable to do mechanically with a plain-text
  heuristic; left to the model via the improved prompt instead.
- **A general French stopword list** instead of the conservative connector-only set. Rejected:
  risks eating meaningful short words that happen to also be common French function words in some
  other sense; kept to words that only ever appear as grammatical glue in a joined segment.
- **Cache/limit the `scan_proposed_path_segments` scan for performance** as the domain grows.
  Not done now (Simplicity First) - flagged as a known future cost, not a problem yet for a
  personal vault's realistic scale.

## Consequences

- `ExtractedAssertion.proposed_path_segments` is now, in practice, always composed of clean,
  single-word, unaccented, special-character-free segments for the `OllamaProvider` path -
  verified in production (see TASK-001e's ticket "Verification record" for the exact before/after
  counts): 0 of 81 segments in the re-verification run contained anything outside `[a-z0-9]`,
  down from segments containing `&`, accents, and multi-word compounds in the pre-amendment run.
- Folder-name convergence improved measurably: 38 distinct paths across 81 assertions in one note
  (vs. 67 distinct paths across 80 in the same note before this amendment) - direct evidence the
  cross-proposal + in-batch context sources are doing real work, not just the normalizer.
- **Known residual limitation, not fixed by this ADR**: singular/plural and other grammatical
  drift for the same real concept (e.g. `conflit` vs `conflits`) can still produce two distinct
  folders for one concept - the normalizer does not stem or lemmatize words, only cleans
  formatting. Left as a smaller, lower-priority version of ADI-014's own already-documented
  naming-drift limitation.
- No change to `ingest_source`'s or `Provider.extract()`'s signatures - `scan_proposed_path_segments`
  is called internally by `OllamaProvider`, using the same `vault_root`/`domain` context keys
  ADI-014 already added.
- Applies only to the `ingestion/` (Assertions) pipeline's `OllamaProvider`, same scope boundary
  as TASK-001e/ADI-014 - not `extraction/`, and not the reviewer's own manual editing path in
  `review/` (TASK-014's `FolderPathBuilder`/`_validate_path_segments`), which is unchanged and
  still only rejects `/` and `..`.
