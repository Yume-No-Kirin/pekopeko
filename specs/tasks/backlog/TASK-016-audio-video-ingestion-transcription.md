# TASK-016: Audio/Video Ingestion with Transcription (YouTube/TikTok/Instagram, V1)

- **Status**: backlog

## Objective

Add a new ingestion path for audio/video content from a URL — YouTube, TikTok, and Instagram —
transcribed to text (Whisper, local) so the existing assertion-extraction pipeline can run on it
exactly as it does on Markdown today. Extends the "Source originale" section of
`pekopeko-proposal-detail.html`'s already-built React screen (TASK-011, `completed`) with the
per-platform metadata and timestamped transcript panels the mockup shows but that TASK-011
explicitly deferred ("video source-type rendering for YouTube/Instagram/TikTok (TASK-016/TASK-017)
— no reader for any of them exists yet, `source_format` is always `"markdown"` today"). Second
entry of `BACKLOG-CLAUDE-V2.md`'s section 2 to be extracted into a full ticket, written directly
at Cleo's request rather than in strict backlog order (TASK-015 remains the next ticket scheduled
for *implementation* — see `docs/ROADMAP.md`).

Scope is **ingestion (Assertions) only** — `BACKLOG-CLAUDE-V2.md`'s own text for this entry says
only "adds an ingestion path", never extraction (entity/event/relationship). No requirement in
`specs/` asks for audio/video support in `extraction/`; that stays a future ticket if a real need
arises, mirroring the precedent already set by TASK-001a/b/c/d/e (additive to `ingestion/` only,
until `extraction/` had an actual consumer).

## Binding context (references, not duplicated here)

- `specs/ux-design/pekopeko-proposal-detail.html:897-1142`: the three source-type-specific mockup
  blocks this ticket implements — YouTube Short (Plateforme/Titre vidéo/Créateur/URL/Durée/Date
  publication/Transcription disponible, then a `[MM:SS]`-timestamped transcript), Instagram Post
  (Plateforme/Type de post/Compte/URL/Date publication/Texte de légende/Transcription audio, then
  caption text and a separately timestamped audio transcript), TikTok Video (Plateforme/Titre/
  Créateur/URL/Durée/Date publication/Hashtags/Transcription, then a timestamped transcript ending
  in a `#hashtag` block). `pekopeko-proposal-detail.html:832-859` is the common "Source originale"
  table (ID Source/Type de source/Fichier/Ingéré le/Hash contenu) every source type shares —
  unchanged by this ticket except the "Type de source" value.
- `specs/tasks/completed/TASK-011-proposal-detail-screen.md:17-22`: names this ticket (and
  TASK-017) as the reason video source-type rendering and a non-`"markdown"` `source_format` were
  out of scope for TASK-011 — this ticket closes that gap.
- `src/app/ingestion/pipeline.py` (current code, read in full while writing this ticket):
  `ingest_source()` builds its reader registry *inline* (lines 81-82: `SourceReaderRegistry()` +
  `registry.register(".md", MarkdownReader)`), reads content via `registry.read_file(source_path)`
  (line 85), then runs the same duplicate-detection → `provider.extract()` → per-assertion
  `write_proposal_file()` → task-state/event-log sequence this ticket's new `ingest_url()` mirrors.
  Duplicate detection (lines 99-129) hashes **content**, not the source path (`_generate_source_id
  (content)`, `ingestion/storage.py`) — reused as-is by `ingest_url()` on the produced transcript
  text.
- `src/app/ingestion/storage.py:137-183` (`write_source_file`, current code): frontmatter today
  hardcodes `'source_format': 'markdown'` (line 167) and takes only `content: str` +
  `original_filename: str` — no channel for structured per-source metadata (title, creator, URL,
  duration, publish date, hashtags) exists anywhere in the current contract. Confirmed nowhere
  else in the codebase either (`ingestion/providers/base.py`'s `ExtractedAssertion`/
  `ExtractionResult` carry none of this).
- `src/app/ingestion/providers/base.py` (current code): `Provider.extract(text, context) ->
  ExtractionResult` — **unchanged by this ticket**. Whisper transcription is a new stage that runs
  *before* this call, producing the `text` this existing interface already expects; the LLM
  provider never sees a video/audio file, only the transcript, exactly as it never sees a `.md`
  file today, only `MarkdownReader`'s output.
- `src/app/api/routes_ingestion.py:30-52` (`start_ingestion`, current code): the only existing
  ingestion route, `POST /domains/<domain>/ingestions`, requires `source_path` in the JSON body,
  builds a `Path(...)`, mints a `task_id`, and calls `run_in_background(ingest_source, ...)` —
  202 + `{"task_id": ..., "status": "pending"}`. No route accepts a URL today.
- `src/app/review/pipeline.py:112` / `src/app/api/serialization.py:113`: `read_source_file` returns
  the Source file's full frontmatter as a free-form `dict[str, Any]` (`ProposalDetailResult.
  source_frontmatter`), and `proposal_detail_to_dict` serializes it via a plain `asdict(detail)` —
  **any new key added to the Source frontmatter reaches the frontend automatically**, no new route
  or serialization change needed for the backend half of this ticket's data contract.
- `frontend/src/pages/ProposalDetail.jsx:438-459` (current code): the existing "Source originale"
  `section-card` renders `original_filename`/`content_hash`/`ingested_at` and a plain
  `sourceBody` text preview — no "Type de source" row, no conditional rendering. This ticket
  extends this section rather than replacing it.
- `src/requirements.txt` (current code): only `pyyaml`, `requests`, `python-dotenv`, `flask`,
  `pytest` are pinned — every dependency this ticket needs (`yt-dlp`, a Whisper implementation) is
  new.
- ADI-005 (rule 1): all AI/LLM or non-trivial computation is asynchronous and produces a Proposal,
  never blocking the user — unchanged; this ticket adds a download+transcribe stage *inside* the
  same async task `ingest_source` already runs in, not a new synchronous code path.
- ADI-010: `127.0.0.1`-only bind + shared `X-API-Key` token — the new route follows the same
  security posture as every existing route, no change to `app.py`'s auth wiring.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

Confirmed with Cleo while writing this ticket (the SourceReader protocol's `read(path: Path) ->
str` signature takes only a local file, so none of this was answerable by re-reading `specs/`
alone):

1. **Content origin is a URL that Pekopeko fetches and downloads itself** — not a video/audio file
   the user already downloaded locally. This is why this ticket introduces a new pipeline entry
   point rather than one more `SourceReader` registered in the existing, Path-only registry.
2. **Transcription is local Whisper, fixed** for V1 — no pluggable "TranscriptionProvider"
   abstraction mirroring ADI-008's LLM-provider pattern. Minimal V1 scope, deliberately chosen;
   revisit only if a real need to swap transcription engines appears (same posture ADI-008 itself
   took before it existed).
3. **All three platforms (YouTube, TikTok, Instagram) in V1**, not a reduced YouTube-only first
   slice — matches `BACKLOG-CLAUDE-V2.md`'s text and all three mockup examples.
4. **The downloaded media file (video/audio) is never persisted** — only the transcript text
   becomes the Source file's canonical content, and the media is discarded after transcription.
   Consistent with ADI-001/ADI-002's "canonical files + derived/reconstructible everything else"
   posture: the raw media is trivially re-fetchable from the URL (kept in `source_metadata.url`),
   so keeping a local copy would be pure derived storage with no invariant requiring it.

The following are this ticket's own proposed defaults (not asked of Cleo as an open question) —
flagged here for objection at read time, same posture as TASK-001a's own `temperature` field
decision:

5. **Download tool: `yt-dlp`** (new dependency, `src/requirements.txt`) — the de facto standard
   for pulling audio + metadata from all three target platforms behind one consistent Python
   API/CLI.
6. **Transcription library: `faster-whisper`** (new dependency) rather than the original
   `openai-whisper` package — avoids a full PyTorch dependency, meaningfully lighter for a
   locally-run desktop tool. **`ffmpeg` is a required system-level prerequisite** (not a Python
   package, not vendored by this ticket) for both `yt-dlp`'s audio extraction and
   `faster-whisper`'s decoding — documented in Constraints below, not silently assumed.
7. **New route**: `POST /domains/<domain>/ingestions/url`, body `{"url": str}` — a dedicated route
   next to the existing `POST /domains/<domain>/ingestions`, rather than overloading the existing
   route's body with an either/or `source_path`/`url`. Matches the project's established pattern of
   one new route per new capability (e.g. TASK-015's `/accept-batch`/`/reject-batch` added next to
   `/accept`/`/reject` rather than changing their contract).
8. **Frontend scope**: this ticket implements the three mockup blocks as closely as the data
   yt-dlp/Whisper can realistically provide (see Acceptance criteria). If real-world rendering
   turns out to need per-platform nuance beyond what's specified here, splitting into a backend
   ticket (this one) and a dedicated frontend follow-up is the explicit fallback
   `BACKLOG-CLAUDE-V2.md` itself already names for this entry ("à scinder en deux tickets... si la
   richesse du rendu par plateforme s'avère volumineuse") — not decided in advance here.

## Scope

### Backend (new)

1. New function `ingest_url(vault_root: Path, domain: str, url: str, provider: Provider, state_dir:
   Path = None, task_id: Optional[str] = None) -> IngestionResult` in
   `src/app/ingestion/pipeline.py`, next to `ingest_source` (not replacing it). Mirrors
   `ingest_source`'s exact task-state/event-log discipline (task started → running → content
   acquired → duplicate check → provider extraction → per-assertion proposal write → completed/
   failed, same `TaskState`/`append_task_event` calls at each step) — only the content-acquisition
   step differs (a platform reader's `fetch(url)` instead of `SourceReaderRegistry.read_file
   (source_path)`).
2. New package `src/app/ingestion/remote_readers/` (naming mirrors the existing `readers/`
   package, but keyed by URL host rather than file extension — a deliberately distinct concept,
   not a repurposing of `SourceReaderRegistry`):
   - `base.py`: `RemoteSourceContent` dataclass (`text: str`, `source_format: str`, `metadata:
     dict`); `RemoteSourceReader` Protocol (`fetch(url: str) -> RemoteSourceContent`);
     `RemoteSourceReaderRegistry` mapping a hostname matcher to a reader class, with
     `get_reader_for_url(url)` resolving by parsed hostname (`youtube.com`/`youtu.be` →
     `YouTubeReader`, `tiktok.com` → `TikTokReader`, `instagram.com` → `InstagramReader`; any other
     host raises `UnsupportedUrlError`, a new exception in `ingestion/errors.py` if that file
     exists, or defined locally otherwise — mirrors the existing `ValueError` a missing
     `SourceReader` extension raises today).
   - `youtube_reader.py` / `tiktok_reader.py` / `instagram_reader.py`: each (a) invokes `yt-dlp` to
     download the audio track plus available metadata (title, uploader/creator handle, duration,
     upload date, description/caption; hashtags parsed from the caption/description where the
     platform embeds them inline, e.g. TikTok/Instagram captions), (b) transcribes the downloaded
     audio via `faster-whisper`, (c) formats the transcript as `[MM:SS] <segment text>` blocks
     separated by a blank line (matching the mockup's exact format), (d) deletes the downloaded
     media file once transcription completes (see V1 scope decision 4), (e) returns a
     `RemoteSourceContent` with `text` = the formatted transcript, `source_format` = `"youtube"` /
     `"tiktok"` / `"instagram"`, and `metadata` = `{"platform": ..., "title": ..., "creator": ...,
     "url": url, "duration_seconds": ..., "published_at": ..., "hashtags": [...] | None, "caption":
     ... | None}` (caption/hashtags populated only for Instagram/TikTok, `None` for YouTube — the
     mockup shows no caption field for the YouTube example).
3. `write_source_file` (`src/app/ingestion/storage.py`) gains two new parameters:
   `source_format: str = "markdown"` (replaces the hardcoded literal on line 167 — default
   preserves every existing call site's behavior unchanged) and `source_metadata: Optional[dict] =
   None`, written into the frontmatter as a `source_metadata` key **only when not `None`**
   (omitted entirely otherwise — existing Markdown-ingestion frontmatter stays byte-identical).
4. `ingest_url` calls the resolved `RemoteSourceReader.fetch(url)`, then runs the *exact same*
   duplicate-detection (`_generate_source_id(content)` on the transcript text, not the URL — two
   different URLs producing an identical transcript are treated as the same source, an accepted
   consequence of reusing the existing content-hash helper unchanged) and
   provider-extraction/proposal-writing logic `ingest_source` already has, passing the new
   `source_format`/`source_metadata` through to `write_source_file`.
5. New route `POST /domains/<domain>/ingestions/url` in `src/app/api/routes_ingestion.py` — body
   `{"url": str}` (missing/blank `url` → existing-style `ValueError`, same 400 mapping as
   `source_path` today), same `202` + `{"task_id": ..., "status": "pending"}` contract as
   `start_ingestion`, dispatching to `run_in_background(ingest_url, _vault_root(), domain, url,
   provider, state_dir, task_id)`. Polling reuses the **existing** `GET
   /domains/<domain>/ingestions/<task_id>` route unchanged (task state has no notion of which
   ingestion function produced it).
6. New dependencies in `src/requirements.txt`: `yt-dlp`, `faster-whisper` (see V1 scope decisions
   5-6 above for rationale; `ffmpeg` documented as a system prerequisite in Constraints, not a pip
   entry).

### Frontend

7. `frontend/src/pages/ProposalDetail.jsx`'s "Source originale" section (lines 438-459) gains a
   "Type de source" row, derived from `source_frontmatter.source_format`: `"markdown"` → "📄
   Fichier Markdown" (existing behavior, now explicit rather than implicit), `"youtube"` → "🎥
   YouTube Short", `"tiktok"` → "🎵 TikTok Video", `"instagram"` → "📱 Instagram Post" (labels/
   emoji taken verbatim from the mockup).
8. New component `frontend/src/components/VideoSourceMetadata.jsx`, rendered inside the same
   "Source originale" `section-card` only when `source_format` is one of the three platforms,
   reading `source_frontmatter.source_metadata`:
   - Metadata table: Plateforme (repeats the Type de source label) / Titre / Créateur / URL (as a
     link) / Durée (formatted `M:SS` from `duration_seconds`) / Date publication (formatted from
     `published_at`) — plus Hashtags (TikTok only, space-joined `#tag` list) and Texte de légende +
     "Transcription audio" availability line (Instagram only) — matching each platform's mockup
     block exactly (`pekopeko-proposal-detail.html:897-1142`).
   - Transcript panel: renders `sourceBody` (already available, unchanged plumbing) inside a
     `max-height` scrollable block identical in structure to the existing Markdown
     `source-preview`, since the transcript's `[MM:SS]` formatting is already produced server-side
     by the reader (no client-side timestamp parsing needed).
   - For Instagram specifically, the mockup shows *two* text blocks (caption, then a separately
     labeled "Transcription audio (voix-off du Reel)") — both come from the same `sourceBody`+
     `metadata.caption` pair (`caption` rendered first as its own block, `sourceBody` — the Whisper
     transcript — rendered second under "Transcription audio").

## Requirements

- **Backend**: Python only (ADI-007). New dependencies confined to `yt-dlp`/`faster-whisper`
  (Requirement note: this ticket introduces the project's first *runtime* dependency needing a
  non-Python system binary, `ffmpeg` — flagged, not hidden).
- **Frontend**: React function components, existing `frontend/src/api/*.js` wrapper style — one
  new thin wrapper (e.g. `startUrlIngestion(domain, url)` → `POST .../ingestions/url`) alongside
  the existing `startIngestion`.

## Constraints

- No change to `ingest_source`, the existing `SourceReader`/`SourceReaderRegistry` contract, or any
  existing route's request/response shape.
- No change to `Provider.extract()`'s interface (`ingestion/providers/base.py`) — Whisper output is
  plain text handed to the existing, unchanged LLM provider call.
- No pluggable transcription-provider abstraction in V1 (scope decision 2).
- No persistence of downloaded media files (scope decision 4) — a failed transcription must not
  leave an orphaned media file on disk; the reader is responsible for its own cleanup even on
  error (e.g. `try`/`finally`).
- **Known, accepted limitation, not addressed here**: downloading third-party platform content via
  a tool like `yt-dlp` intersects with those platforms' terms of service. Out of scope for a
  technical ticket to resolve, but named explicitly rather than silently assumed away — same
  posture as other "known limitation, not fixed" notes already in `docs/ROADMAP.md` (e.g.
  ADI-014/ADI-015).
- No entity/event/relationship (extraction/) support — ingestion (Assertions) only (see Objective).

## Files/modules concerned

- **Backend** (new): `src/app/ingestion/remote_readers/base.py`, `youtube_reader.py`,
  `tiktok_reader.py`, `instagram_reader.py`.
- **Backend** (modified in place): `src/app/ingestion/pipeline.py` (new `ingest_url`),
  `src/app/ingestion/storage.py` (`write_source_file` gains `source_format`/`source_metadata`
  params), `src/app/api/routes_ingestion.py` (new `/ingestions/url` route), `src/requirements.txt`
  (new deps).
- **Backend** (new tests): `src/tests/ingestion/test_remote_readers.py`,
  `src/tests/ingestion/test_ingest_url.py` (or additions to the existing `test_pipeline.py`,
  matching this project's file-granularity conventions), `src/tests/api/test_ingestion_routes.py`
  additions.
- **Frontend** (new): `frontend/src/components/VideoSourceMetadata.jsx` +
  `VideoSourceMetadata.test.jsx`.
- **Frontend** (modified in place): `frontend/src/pages/ProposalDetail.jsx`,
  `frontend/src/pages/ProposalDetail.test.jsx`, `frontend/src/api/ingestion.js` (or equivalent
  existing wrapper file — new `startUrlIngestion` export).
- No file under `src/app/extraction/` or `src/app/review/` is touched.

## Dependencies

- None on other backlog tickets — independent, buildable on top of already-`completed` TASK-001/
  TASK-007/TASK-011.
- `TASK-017`'s "web page" reader (backlog, written alongside this ticket) reuses this ticket's
  `RemoteSourceReader`/`RemoteSourceReaderRegistry` infrastructure for its own generic-URL case —
  TASK-017 depends on this ticket for that part only; its PDF/plain-text readers do not.

## Acceptance criteria

1. `ingest_url()` called with a fake `RemoteSourceReader` registered for a test host produces the
   same `IngestionResult` shape (`source_id`, `proposal_ids`, `status`) as `ingest_source()` does
   for an equivalent fixed piece of content — same success/failure/duplicate semantics.
2. The Source file written for a URL ingestion has `source_format` matching the resolved platform
   (`"youtube"`/`"tiktok"`/`"instagram"`) and a `source_metadata` dict containing at least
   `platform`/`title`/`creator`/`url`/`duration_seconds`/`published_at`.
3. A Markdown ingestion via the existing `ingest_source()` produces byte-identical frontmatter to
   before this ticket (`source_format: "markdown"`, no `source_metadata` key present) — confirms
   the new parameters' defaults are fully backward-compatible.
4. Two different URLs whose fetched transcripts are identical are detected as a duplicate on the
   second call (same content-hash-based semantics as `ingest_source`).
5. `POST /domains/<domain>/ingestions/url` with a valid `url` returns `202` with a `task_id`;
   `GET /domains/<domain>/ingestions/<task_id>` on that id eventually reports `completed` (fake
   reader/provider in tests, no real network/yt-dlp/Whisper call).
6. `POST /domains/<domain>/ingestions/url` with a missing or blank `url` returns `400`.
7. An unsupported host (not YouTube/TikTok/Instagram) raises `UnsupportedUrlError`, surfaced as a
   failed task state with a message naming the unsupported host — not a silent no-op.
8. A reader whose transcription step raises leaves no downloaded media file on disk afterward
   (verified via a fake reader that creates a temp file and asserts its own cleanup ran, or via a
   `tmp_path`-scoped download directory left empty after a forced failure).
9. `ProposalDetail.jsx` given a fixture proposal whose source has `source_format: "youtube"` (resp.
   `tiktok`, `instagram`) renders the "Type de source" label and the matching
   `VideoSourceMetadata` fields (title/creator/url/duration/published date, plus hashtags for
   TikTok, plus caption for Instagram) exactly as the mockup shows; a `"markdown"` fixture renders
   unchanged from TASK-011's existing behavior.
10. `git status --porcelain -- src/app/extraction/ src/app/review/` is empty after implementation.

## Testing requirements

- **Backend**: `pytest`, `tmp_path` fixtures. No real network call, no real `yt-dlp` invocation, no
  real Whisper model load — platform readers are tested via a fake `RemoteSourceReader`
  implementation (same spirit as the existing `FixedIngestionProvider`/`FakeIngestionProvider`
  patterns in `src/tests/acceptance/_acceptance_helpers.py` / `src/tests/api/_helpers.py`); if the
  concrete `YouTubeReader`/etc. classes are unit-tested directly, `yt-dlp`'s and
  `faster-whisper`'s calls are mocked at the module boundary, never executed for real. Coverage
  discipline (≥80%, AGENTS.md) applies to every new/touched file.
- **Frontend**: same mocked-`fetch`/React Testing Library pattern as `ProposalDetail.test.jsx`
  (TASK-011), extended with youtube/tiktok/instagram fixtures for AC9; no real network calls.

## Out of scope

- A pluggable "TranscriptionProvider" abstraction (scope decision 2) — local Whisper only.
- Any platform beyond YouTube/TikTok/Instagram.
- `extraction/` (entity/event/relationship) support for audio/video sources.
- Persisting the downloaded media file, or any user-facing media playback (audio/video player) in
  the frontend — only the transcript and metadata are shown, per the mockup.
- Editing transcribed content beyond what TASK-013's existing edit mode already allows for any
  assertion.
- Resolving the platform-ToS question named in Constraints.
