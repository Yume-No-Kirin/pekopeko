# ADI-007: Implementation Language for the Knowledge Core

- **ID**: ADI-007
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`specs/product/scope.md` explicitly lists "no final database technology", "no final frontend framework decision... unless already present in the repository", and "no final LLM provider architecture" as open questions for the foundation phase, and `specs/decisions/README.md` classifies "Technology stack selections" as a category of decision that must be recorded as an ADR. The repository contains no existing code (confirmed by listing the repo root on 2026-08-16: only `specs/`, `docs/`, `.git/`, `.gitignore`, `README.md`, `temp/`), so "already present in the repository" does not resolve anything. This was not one of the six ADI questions from `technical-requirements.md` section 23 (ADI-001 through ADI-006) — it became a blocking gap only once Phase 2 required writing the first implementable ticket for qwen3-coder:30b: none of ADI-001 through ADI-006 specify what language the Knowledge Core (canonical file storage, per-item history, retrieval index, relationship adjacency, async task state) should be implemented in.

## Decision

The Knowledge Core — and, by default, the rest of the backend/system logic unless a future ADR says otherwise — is implemented in **Python**.

Reasoning, grounded in the decisions already made:
- ADI-001/ADI-002 established a file-based canonical store with SQLite/FTS5 as the first derived index technology. Python's standard library ships `sqlite3` and has mature file/YAML-frontmatter handling, so this core layer needs no exotic runtime dependency.
- The system's central purpose is AI/LLM-driven ingestion, extraction, and reasoning (per the canonical conceptual flow in `specs/domain/knowledge-model.md`). Python has the broadest, most mature AI/LLM ecosystem of any mainstream language today (local embeddings, model tooling, orchestration libraries).
- qwen3-coder:30b — the model expected to implement most Phase 3 tickets — has broad, well-represented Python training data, which reduces implementation risk for delegated tickets.
- Pekopeko runs entirely local-first on Cleo's own machine — Python is fully cross-platform and needs no build/compile step, keeping iteration fast for a personal project still in its foundation phase.

This decision is scoped to the Knowledge Core and backend logic. It does **not** decide a frontend/GUI framework (`module-architecture.md`'s "unified Pekopeko application interface" remains an open question for a later ADR, once GUI work is actually scoped) nor an LLM provider architecture (also explicitly out of scope per `scope.md`).

## Alternatives considered

- **TypeScript/Node.js.** Rejected for the Knowledge Core specifically: no compelling advantage over Python for file/SQLite-heavy backend logic, and its AI/LLM ecosystem is comparatively less mature today. Remains a live option for a future GUI layer — that is a separate decision, not foreclosed by this ADR.
- **Rust, Go, or another systems language.** Rejected: nothing in the specs establishes a performance requirement that would justify the added implementation complexity and slower iteration, for what is, per `scope.md`, still a foundation-phase personal project of unknown final scale.

## Consequences

- Every Phase 2 ticket must specify Python-implementable requirements (module structure, testing via `pytest`, dependencies declared explicitly) so qwen3-coder:30b has an unambiguous target.
- A future GUI/frontend decision is not implied or pre-empted by this ADR and must be made separately once that work is actually scoped.
- If a future component has a genuine, specific reason to use a different language (e.g. a performance-critical derived index), that should be its own ADR scoped to that component, not a silent deviation from this default.
