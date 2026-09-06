# TASK-017: Additional Source Readers — PDF, Plain Text, Web Page (V1)

- **Status**: backlog

## Objective

Add three new source formats to the extensible reader registries already established by TASK-001
(ingestion) and TASK-003 (extraction): PDF, plain text, and web page. Closes the other half of the
gap TASK-011 explicitly deferred ("video source-type rendering for YouTube/Instagram/TikTok
(TASK-016/TASK-017) — no reader for any of them exists yet, `source_format` is always `"markdown"`
today"). Third entry of `BACKLOG-CLAUDE-V2.md`'s section 2 to be extracted into a full ticket,
written directly at Cleo's request alongside TASK-016 rather than in strict backlog order
(TASK-015 remains the next ticket scheduled for *implementation* — see `docs/ROADMAP.md`).

Two of the three readers (PDF, plain text) are straightforward extensions of the existing,
Path-only `SourceReader` contract — exactly what `BACKLOG-CLAUDE-V2.md`'s text for this entry
describes ("no pipeline modification required by construction"), modulo one small, real exception
(the hardcoded `source_format`, see Binding context). The third (web page) is **not** — see V1
scope decisions below for why it depends on TASK-016 instead.

## Binding context (references, not duplicated here)

- `src/app/ingestion/readers/base.py` / `src/app/extraction/readers/base.py` (current code, read
  in full): identical `SourceReader` Protocol (`read(path: Path) -> str`) and
  `SourceReaderRegistry` (extension → reader class), deliberately duplicated rather than shared
  (extraction's own docstring: "Independent of app/ingestion/readers/ - reimplemented rather than
  imported"). `src/app/ingestion/readers/markdown_reader.py`'s `MarkdownReader.read()` does
  nothing Markdown-specific — it opens the file as UTF-8 text and returns it verbatim, which is
  exactly what a plain-text reader would do too (see Scope item 1).
- `src/app/extraction/pipeline.py:43-46` (`_build_reader_registry()`, current code): the one place
  extraction registers `.md` → `MarkdownReader`. `src/app/ingestion/pipeline.py:81-82` (current
  code): the equivalent registration, but inline inside `ingest_source()` rather than a dedicated
  function — both are extended identically by this ticket (one new `.register(...)` call per new
  extension, in each module).
- **Real gap not mentioned by `BACKLOG-CLAUDE-V2.md`'s "no pipeline modification required"
  framing**: `write_source_file` hardcodes `'source_format': 'markdown'` in both
  `src/app/ingestion/storage.py:167` and `src/app/extraction/storage.py:126` — confirmed while
  writing this ticket (and TASK-016, written the same session) by reading both functions in full.
  Without a real parameter, any file ingested through a new reader would still report
  `source_format: "markdown"` in its frontmatter, which is wrong and would mislead the frontend's
  "Type de source" rendering (see Scope item 4 and TASK-016's identical fix — the same
  `write_source_file` signature change is shared by both tickets, done once if TASK-016 lands
  first, reused as-is here otherwise).
- `src/requirements.txt` (current code): only `pyyaml`, `requests`, `python-dotenv`, `flask`,
  `pytest` are pinned — PDF parsing and HTML parsing are both new dependencies.
- `frontend/src/pages/ProposalDetail.jsx:438-459` (current code): the "Source originale" section
  this ticket extends the same way TASK-016 does (see that ticket's Scope item 7) — a "Type de
  source" row plus, here, no dedicated per-type metadata panel (the mockup has none for PDF/plain
  text/web page — see V1 scope decision 3 below).
- `specs/tasks/completed/TASK-011-proposal-detail-screen.md:17-22`: names this ticket (and
  TASK-016) as the reason non-Markdown `source_format` rendering was out of scope for TASK-011.

## V1 scope decisions (explicit — flag disagreement, don't silently deviate)

Confirmed with Cleo while writing this ticket (alongside TASK-016, same session):

1. **The web page reader fetches a URL itself** (Pekopeko downloads the page), not a local `.html`
   file the user already saved. Same architectural fork as TASK-016's video/audio content: the
   existing `SourceReader.read(path: Path)` contract cannot express "fetch a remote URL", so this
   one reader does **not** register into the existing, Path-only `SourceReaderRegistry`.

Consequence of that decision, spelled out rather than silently absorbed:

2. **The web page reader reuses TASK-016's new `RemoteSourceReaderRegistry`/`RemoteSourceReader`
   infrastructure** (`src/app/ingestion/remote_readers/`, introduced by that ticket for
   YouTube/TikTok/Instagram) rather than inventing a second, parallel URL-fetch mechanism. A new
   `WebPageReader` is registered there as the fallback for any `http(s)://` host that isn't one of
   the three platform hosts. **This makes the web-page part of this ticket dependent on TASK-016**
   — a real dependency this ticket did not have in `BACKLOG-CLAUDE-V2.md`'s original framing (which
   presented TASK-016/TASK-017 as independent). The PDF and plain-text readers below have no such
   dependency; they are ordinary `SourceReader(path)` extensions, buildable and shippable on their
   own even if TASK-016 is never implemented.
3. **No dedicated per-format metadata panel for PDF/plain text/web page** — unlike TASK-016's three
   mockup blocks, `pekopeko-proposal-detail.html` shows no example for these formats. V1 renders
   only a "Type de source" label change (see Scope item 7) plus the existing generic text preview,
   reused as-is. If Cleo wants more (e.g. a page count for PDF, the fetched page's own `<title>`
   for web page) at read time, that's additive scope for a follow-up, not guessed here.
4. **PDF library: `pypdf`** (new dependency) — pure Python, permissive (BSD-style) license, no
   native/binary build step, widely used for straightforward text extraction. Proposed default,
   flagged for objection at read time, same posture as TASK-016's `yt-dlp`/`faster-whisper` picks.
5. **HTML parsing library: `beautifulsoup4`** (new dependency) for the web page reader —
   `requests` (already pinned) handles the HTTP fetch itself.

## Scope

### Backend (new) — PDF and plain text (independent of TASK-016)

1. `src/app/ingestion/readers/plaintext_reader.py` / `src/app/extraction/readers/
   plaintext_reader.py`: `PlainTextReader.read(path) -> str` — opens the file as UTF-8 text and
   returns it verbatim. Functionally identical to `MarkdownReader` today (neither does anything
   format-specific); kept as its own class rather than reusing `MarkdownReader` under a second
   extension, so the two remain independently evolvable (e.g. if Markdown-specific preprocessing is
   ever added, plain text must not silently inherit it).
2. `src/app/ingestion/readers/pdf_reader.py` / `src/app/extraction/readers/pdf_reader.py`:
   `PdfReader.read(path) -> str` — extracts and concatenates text from every page via `pypdf`,
   pages joined by a blank line. A PDF with no extractable text layer (scanned image, no OCR)
   returns an empty string, which the existing pipeline already treats as "Source file is empty"
   (ADI-011's zero-output handling, `TASK-001c`/`TASK-003`'s equivalent check) — no new empty-
   content handling needed here, the existing check covers it.
3. Both new readers registered in `src/app/ingestion/pipeline.py` (inline registry in
   `ingest_source()`, `.txt` → `PlainTextReader`, `.pdf` → `PdfReader`) and
   `src/app/extraction/pipeline.py` (`_build_reader_registry()`, same two registrations) —
   four `.register(...)` lines total, no other change to either pipeline function.

### Backend (new) — Web page (depends on TASK-016)

4. `write_source_file` in both `src/app/ingestion/storage.py` and `src/app/extraction/storage.py`
   gains the same `source_format`/`source_metadata` parameters TASK-016 introduces (shared change
   — implemented once, by whichever of the two tickets lands first; the other reuses it as-is
   rather than re-specifying it).
5. `src/app/ingestion/remote_readers/webpage_reader.py`: `WebPageReader.fetch(url) ->
   RemoteSourceContent` (same dataclass TASK-016 defines) — fetches the URL via `requests`, parses
   the HTML via `beautifulsoup4`, strips script/style/nav/footer elements, and returns the visible
   text content joined with blank lines between block-level elements. `metadata` = `{"url": url,
   "title": <page's own <title> tag, or None>}` — no duration/creator/hashtags (none apply to a
   generic web page). `source_format = "web_page"`.
6. Registered in `RemoteSourceReaderRegistry` (TASK-016) as the fallback for any `http(s)://` host
   not already claimed by YouTube/TikTok/Instagram.
7. New dependency in `src/requirements.txt`: `pypdf`, `beautifulsoup4` (see V1 scope decisions 4-5).

### Frontend

8. `frontend/src/pages/ProposalDetail.jsx`'s "Type de source" row (introduced by TASK-016, or by
   this ticket if TASK-016 has not landed yet — same shared change either way) gains three more
   cases: `"pdf"` → "📄 Document PDF", `"txt"` → "📄 Fichier texte", `"web_page"` → "🌐 Page web".
   No other frontend change — see V1 scope decision 3 (no dedicated metadata panel for these three
   formats).

## Requirements

- **Backend**: Python only (ADI-007). `pypdf`/`beautifulsoup4` are the only new dependencies for
  the PDF/plain-text/web-page readers themselves (the web-page reader's URL-fetch machinery is
  TASK-016's `yt-dlp`/`faster-whisper` dependencies plus `requests`, already pinned — this ticket
  adds none of its own for that part beyond `beautifulsoup4`).
- **Frontend**: one-line addition to an existing label-mapping structure, no new component.

## Constraints

- No change to `ingest_source`/`extract_source`'s existing control flow beyond the new
  `.register(...)` calls and the `write_source_file` parameter addition (shared with TASK-016).
- No change to `SourceReader`/`SourceReaderRegistry`'s existing Protocol/class shape — the three
  new local-file readers (`PlainTextReader`, `PdfReader`, and the two existing/untouched
  `MarkdownReader`s) all implement it unchanged.
- The web page reader is **not** a `SourceReader` — it must not be registered in
  `SourceReaderRegistry`; registering it there would silently violate the Path-only contract every
  other reader in that registry relies on.
- No dedicated metadata panel for PDF/plain text/web page in V1 (scope decision 3).

## Files/modules concerned

- **Backend** (new): `src/app/ingestion/readers/plaintext_reader.py`,
  `src/app/ingestion/readers/pdf_reader.py`, `src/app/extraction/readers/plaintext_reader.py`,
  `src/app/extraction/readers/pdf_reader.py`, `src/app/ingestion/remote_readers/
  webpage_reader.py` (depends on TASK-016's `remote_readers/base.py`).
- **Backend** (modified in place): `src/app/ingestion/pipeline.py`, `src/app/extraction/
  pipeline.py` (new `.register(...)` calls only), `src/requirements.txt`. `write_source_file` in
  both `storage.py` files only if not already changed by TASK-016 (shared parameter addition, not
  duplicated).
- **Backend** (new tests): `src/tests/ingestion/test_plaintext_reader.py`,
  `src/tests/ingestion/test_pdf_reader.py`, mirrored under `src/tests/extraction/`, plus
  `src/tests/ingestion/test_webpage_reader.py`.
- **Frontend** (modified in place): `frontend/src/pages/ProposalDetail.jsx`,
  `frontend/src/pages/ProposalDetail.test.jsx` (3 new fixture cases).
- No file under `src/app/review/` is touched.

## Dependencies

- **TASK-016** (backlog, written the same session): required for the web-page reader only (shares
  `remote_readers/base.py`'s `RemoteSourceReader`/`RemoteSourceReaderRegistry` and the
  `write_source_file` parameter addition). The PDF and plain-text readers have no dependency on
  TASK-016 and can be implemented and shipped independently of it — if TASK-016 is deprioritized,
  this ticket's scope reduces to items 1-3 + 8 (minus the `"web_page"` case) rather than blocking
  entirely.
- Independent of TASK-013/TASK-014/TASK-015 (edit mode, folder-path builder, bulk operations) — no
  interaction with any of them.

## Acceptance criteria

1. A `.txt` file ingested via `ingest_source()` produces a Proposal identical in shape to a `.md`
   ingestion of the same text content, with `source_format: "txt"` on its Source file.
2. A `.pdf` file with extractable text ingested via `ingest_source()` produces a Proposal with
   `source_format: "pdf"` and Source content equal to the concatenated per-page text.
3. A `.pdf` with no extractable text fails the same way an empty `.md`/`.txt` source does today
   ("Source file is empty", per ADI-011) — no new/different error path introduced.
4. The same two readers (`.txt`, `.pdf`) registered in `extract_source()` produce entity/event/
   relationship Proposals with `source_format` set identically to their `ingestion/` counterpart,
   confirmed against `src/app/extraction/storage.py::REQUIRED_SOURCE_FIELDS`.
5. A URL resolved by `RemoteSourceReaderRegistry` to something other than YouTube/TikTok/Instagram
   is fetched by `WebPageReader`, producing `source_format: "web_page"` and Source content equal to
   the page's visible text (script/style/nav/footer excluded), verified against a fixture HTML page
   with known extractable text.
6. `ProposalDetail.jsx` given fixtures with `source_format` of `"pdf"`, `"txt"`, and `"web_page"`
   renders the corresponding "Type de source" label from Scope item 8 and otherwise renders
   identically to a `"markdown"` fixture (same generic preview, no extra panel).
7. `git status --porcelain -- src/app/review/` is empty after implementation.
8. `write_source_file`'s new `source_format`/`source_metadata` parameters are changed in exactly
   one place shared with TASK-016 if that ticket is implemented first — not duplicated as a second,
   divergent change.

## Testing requirements

- **Backend**: `pytest`, `tmp_path` fixtures — a real short PDF fixture (generated at test time or
  checked in as a small binary fixture, project's choice at implementation time) for AC2/AC3, a
  plain fixture HTML string for AC5 (`WebPageReader` tested via a mocked `requests.get`, no real
  network call — same discipline as TASK-016's fake-reader testing posture). Coverage discipline
  (≥80%, AGENTS.md) applies to every new/touched file.
- **Frontend**: same mocked-`fetch`/React Testing Library pattern as `ProposalDetail.test.jsx`.

## Out of scope

- Any dedicated per-format metadata panel for PDF/plain text/web page beyond the "Type de source"
  label (scope decision 3).
- OCR for scanned/image-only PDFs.
- Any other document format (DOCX, EPUB, images, etc.) — not requested by `BACKLOG-CLAUDE-V2.md`'s
  text for this entry.
- Re-fetching or re-validating a web page's content after ingestion (staleness/change detection is
  TASK-026's concern, not this ticket's).
