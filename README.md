# Pekopeko

Personal AI environment: a Knowledge Core that ingests personal notes (currently
Markdown files in an Obsidian vault), extracts structured knowledge (Assertions,
Entities, Events, Relationships) via a pluggable LLM provider, and routes every
extraction through a human review queue before anything is written canonically.
See [specs/product/vision.md](specs/product/vision.md) for the long-term product
direction.

## Start here, not below

This README only covers **environment setup** — cloning, installing, running
the app locally. It does not describe project state, decisions, or what to work
on next. For that:

1. Read [AGENTS.md](AGENTS.md) in full — it is the canonical instructions file,
   read natively by every agent working in this repo (Claude Code, Codex CLI,
   qwen3-coder).
2. Then read [docs/ROADMAP.md](docs/ROADMAP.md) in full — the single source of
   continuity: current phase, accepted architecture decisions (ADRs), ticket
   status, and the exact next action.

Do not rely on this README, or on memory of a previous conversation, for either
of those — both drift, and ROADMAP.md is kept current after every session.

## Prerequisites

- Python 3.x with `pip`, available on `PATH`
- Node.js with `npm`, available on `PATH`
- (Optional, for real LLM extraction) a local [Ollama](https://ollama.com) instance

## Quick start (Windows)

From the repo root:

```
start-pekopeko.bat
```

On first run this generates `.pekopeko-local.env` (gitignored — vault root under
`%USERPROFILE%\.pekopeko\vault`, a random API key) and a matching
`frontend\.env`, installs Python and npm dependencies, then launches the Flask
backend and the Vite frontend dev server each in their own window and opens the
dashboard at `http://localhost:5173`.

## Manual setup

1. Copy the env template and fill in your own values:

   ```
   copy .pekopeko-local.env.example .pekopeko-local.env
   ```

   - `PEKOPEKO_VAULT_ROOT` — absolute path to your Obsidian vault (or any
     folder to use as the canonical knowledge store). The backend refuses to
     start without it.
   - `PEKOPEKO_API_KEY` — shared secret required on every API request
     (`X-API-Key` header). The backend binds to `127.0.0.1` only — see
     `specs/decisions/ADI-010-...md` for the full security model.

2. Load those variables into your shell, then install and run the backend
   from the repo root (imports are package-relative, so it must run as a
   module):

   ```
   pip install -r src/requirements.txt
   python -m src.app.api.app
   ```

   Backend serves on `http://127.0.0.1:5000`.

3. In a second terminal, create `frontend\.env`:

   ```
   VITE_API_BASE_URL=http://127.0.0.1:5000
   VITE_API_KEY=<same value as PEKOPEKO_API_KEY>
   ```

   Then install and run the frontend:

   ```
   cd frontend
   npm install
   npm run dev
   ```

   Frontend serves on `http://localhost:5173`.

## Tests

Backend (from repo root, `pytest.ini` excludes `e2e` by default since those
need a live Ollama):

```
pytest src/tests
```

Run end-to-end tests explicitly (requires a real local Ollama):

```
pytest -m e2e
```

Frontend:

```
cd frontend
npm test
```

## Repository layout

- `AGENTS.md` — canonical agent instructions (read first, see above)
- `docs/ROADMAP.md` — current phase, decisions, ticket status, next action
- `specs/` — product vision, architecture, domain model, ADRs
  (`specs/decisions/`), tickets (`specs/tasks/{backlog,active,completed}/`)
- `src/app/` — Python backend (ingestion, extraction, review, config, api)
- `src/tests/` — backend tests (`acceptance/` deterministic, `e2e/` real Ollama)
- `frontend/` — React + Vite frontend
- `scripts/` — launch scripts used by `start-pekopeko.bat`
- `graphify-out/` — generated knowledge graph of this codebase (see
  `AGENTS.md`'s graphify section)
