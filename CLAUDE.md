# CLAUDE.md

## First thing, every session

Read `docs/ROADMAP.md` in full before touching anything in this repo. It is the single source of continuity — not this file, not `docs/PROJECT_HANDOFF.md` (a stale one-off dump, explicitly not kept up to date, do not rely on it). Then follow ROADMAP.md's own "Démarrage de session" steps: find the current phase, read that phase's "Lecture requise" file list in full (not a summary), and check `specs/decisions/` for ADRs relevant to that phase.

## Source of truth

- `docs/ROADMAP.md` — current phase, status, next action. Kept up to date; trust it over memory of past conversations.
- `specs/` — product vision, architecture, domain model, and ADRs. `specs/decisions/README.md` defines the ADR format; `specs/tasks/README.md` defines the ticket lifecycle (`backlog/` → `active/` → `completed/`).
- Everything else (this file included) should point at those two, not duplicate their content — ROADMAP.md itself explains why `PROJECT_HANDOFF.md` went stale by doing that.

## Working conventions

- An ADR with status `Proposed` is not a decision. Never treat it as accepted without Cleo's explicit confirmation, even if the draft already exists.
- After any session that changes something (spec, decision, code), update ROADMAP.md's "État actuel" and "Prochaine action exacte" — and verify the two are still mutually consistent, not just individually edited. A real desync between them happened once (see ROADMAP.md's "Bug trouvé et corrigé dans ce fichier lui-même").
- A ticket under `specs/tasks/` must be self-contained: files/modules concerned, expected schema/interface, testable acceptance criteria, and the 2-3 relevant invariants cited explicitly in the ticket. If implementing a ticket requires re-reading all of `specs/`, the ticket is scoped wrong.
- A significant architecture decision belongs in `specs/decisions/` as a real ADR file — not only as a paragraph in ROADMAP.md or a conclusion left in chat history.
- Verification discipline: never trust a single test run or an AI-generated report at face value. Reproduce independently — copy the code to an isolated location, rerun tests yourself, check each acceptance criterion one by one. Write audit/verification reports to a file in a structured, line-by-line format (`[STATUS] check — result`), listing every check attempted including ones that failed to run — not summarized in chat.

## Coding Discipline

**Think Before Coding**
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

**Simplicity First**
- Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked, no abstractions for single-use code, no "configurability" that wasn't requested.
- No error handling for scenarios that can't happen in a `tools/` script.

**Surgical Changes**
- Touch only what the task requires. Don't "improve" adjacent code, comments, or formatting in a tool/workflow you're editing. Match existing style.
- Remove imports/variables/functions that YOUR change made unused. Don't remove pre-existing dead code unless asked — mention it instead.

**Goal-Driven Execution**
- Before writing code, define what "done" looks like as something you can check (a test, a sample run, an expected output) — not just "make it work."
- This is what makes the Self-Improvement Loop below possible: you can't verify a fix or a fresh tool without a concrete success criterion to check it against.

## Code and tests

- Backend implementation language is Python (ADI-007, `specs/decisions/ADI-007-implementation-language.md`).
- No `requirements.txt` or `pyproject.toml` exists yet; the only dependency in use so far is `pyyaml`.
- Tests use `pytest` and must run against a temp directory (`tmp_path` or equivalent) — never against a real Obsidian vault or any path outside the test's own temp directory.
- No git-based historization anywhere in the implementation. Canonical item history is per-item folders on disk (ADI-001, `specs/decisions/ADI-001-canonical-persistence-model.md`) — this was an explicit, firm decision; do not reintroduce git for it.
- Test coverage : at least 80%

## Language

`docs/ROADMAP.md` and session-continuity notes are written in French (for Cleo, the project owner). `specs/` and code/comments are in English. Match whichever a given file already uses — don't convert one to the other.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Windows Encoding Rules

This environment is Windows. Silent encoding mismatches between Python, PowerShell, and git are the #1 source of mangled accented characters and corrupted files — always write UTF-8 without a BOM, explicitly.

- **Python tools**: always open files with an explicit `encoding="utf-8"` — never rely on the Windows default locale (cp1252/mbcs), which mangles accented/French characters.
- **Never write a BOM**: use `encoding="utf-8"` (not `"utf-8-sig"`) when writing files meant for git, JSON, or APIs to consume. `utf-8-sig` is only for *reading* files that may already carry a BOM (Excel exports, some PowerShell output).
- **CSV**: open with `newline=""` on Windows to avoid blank rows from the csv module.
- **PowerShell**: `Out-File`, `Set-Content`, and `>` default to UTF-8 **with BOM** on Windows PowerShell 5.1. Don't route data destined for Python/JSON through them — write files from Python instead, or if PowerShell must write text, use `[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding $false))`.
- **When unsure**, check a file's first bytes for `EF BB BF` before trusting it downstream.
