# ADI-009: Frontend Framework for the Pekopeko Application Interface

- **ID**: ADI-009
- **Date**: 2026-08-29
- **Status**: Accepted (confirmed by Cleo on 2026-08-29)

## Context

`specs/product/scope.md` explicitly listed "no final frontend framework decision should be assumed unless already present in the repository" as an open question for the foundation phase, and `ADI-007-implementation-language.md` (which decided Python for the Knowledge Core/backend) explicitly scoped itself out of this question: "This decision... does not decide a frontend/GUI framework (`module-architecture.md`'s 'unified Pekopeko application interface' remains an open question for a later ADR, once GUI work is actually scoped)." `docs/ROADMAP.md` (Phase 2, chemin critique) lists "Interface — nécessite une décision de stack frontend, pas encore prise" as the third item blocking a usable walking skeleton, after the proposal workflow and the ingestion pipeline.

Since then, `specs/ux-design/` has been populated with four static, framework-agnostic HTML/CSS/JS mockups (Dashboard, Validation workflow, Ingestion Logs, Proposal Detail) plus a README describing them as a UX specification. These mockups are deliberately not tied to any implementation stack — plain HTML with inline CSS and vanilla JS, full-page navigation between files, no build tooling, no framework references. Several signals in the files themselves confirm they are illustrative only, not production code: `pekopeko-proposal-detail.html` contains the comment "Simulated list of proposal IDs (in a real app, this would come from the server or session storage)", and interactive actions across the mockups (accept/reject a proposal, create a new ingestion) trigger `alert()`/`confirm()`/`prompt()` placeholders rather than real behavior. They do, however, define concrete screens and interaction patterns worth carrying forward: a unified dashboard, a validation view grouping proposals by source with an interactive folder-path builder, an ingestion log table, and a proposal detail view with source-type-specific rendering (Markdown/YouTube/Instagram/TikTok).

With this UX groundwork in place, the frontend framework choice is no longer premature to make, and leaving it open continues to block the "Interface" item of the Phase 2 critical path.

## Decision

**ReactJS** is the frontend framework for Pekopeko's unified application interface (the "unified Pekopeko application interface" referenced in `specs/modules/module-architecture.md`).

Reasoning:
- Team familiarity with React is the primary driver — it avoids the learning-curve cost and implementation risk of adopting an unfamiliar framework, consistent with the pragmatic, already-known-tooling reasoning ADI-007 applied to the backend language choice for this local-first, solo-project foundation phase.
- The UX patterns already sketched in `specs/ux-design/` (a dashboard, a validation view with bulk actions and per-item state, a folder-path builder with dynamic dropdowns, a proposal detail view that swaps rendering based on source type) involve enough client-side state and interactivity that a component-based framework is a better fit than continuing with vanilla JS/full-page navigation.

This decision is scoped to the choice of framework only. It does not scope or ticket the frontend implementation itself — which screens ship in a V1, how the interface talks to the backend, build tooling, routing, and state management remain open and must be defined in a future ticket once that work is actually scoped, the same restraint ADI-007 applied to the backend.

## Alternatives considered

- **Vue or Svelte.** Both are viable component-based frameworks, but neither has existing team familiarity behind it, and nothing in the specs justifies the added learning cost over React at this stage.
- **A native Obsidian plugin/extension as the interface.** Rejected: `ADI-004-obsidian-role.md` already establishes that Pekopeko never uses Obsidian's native mechanisms (graph, backlinks, search, or plugin UI) as an operating mechanism — building the interface as an Obsidian plugin would contradict that decision.
- **Continuing with vanilla HTML/CSS/JS**, extending the style already used in `specs/ux-design/`. Rejected for the real application: acceptable for throwaway mockups, but the interactions those mockups already imply (grouped bulk actions, live folder-path editing, multi-note navigation, dynamic source-type rendering) call for real component state management rather than hand-rolled DOM manipulation across growing global functions.

## Consequences

- `specs/ux-design/` remains the UX/interaction reference (screens, the folder-path-builder pattern, source-type-specific metadata) but its HTML/CSS/JS files are not production code and will need to be reimplemented as React components; `specs/ux-design/README.md` has been updated to note this.
- `specs/product/scope.md` has been updated so it no longer lists the frontend framework as an undecided item, and now points to this ADR.
- No frontend implementation ticket exists yet. This ADR unblocks the framework choice only — the actual V1 interface scope, its ticket(s), build tooling, and how it integrates with the backend (Knowledge Core, ingestion pipeline, proposal review workflow) must still be defined once that work is scoped, per the Phase 2 critical path in `docs/ROADMAP.md`.
