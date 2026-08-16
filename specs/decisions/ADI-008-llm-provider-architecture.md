# ADI-008: LLM Provider Architecture for Runtime Extraction

- **ID**: ADI-008
- **Date**: 2026-08-16
- **Status**: Accepted (confirmed by Cleo on 2026-08-16)

## Context

`specs/product/scope.md` explicitly lists "No final LLM provider architecture should be assumed" as an open question for the foundation phase. The ingestion/extraction pipeline (UC-001, UC-007) needs a concrete LLM to perform atomic-assertion extraction — per `specs/domain/knowledge-model.md`'s conceptual flow (`SOURCE → AI INTERPRETATION / EXTRACTION → PROPOSAL`), this is a genuine AI interpretation step, not classic NLP parsing. This LLM is distinct from qwen3-coder:30b, which is only used to write Pekopeko's own code during development, never invoked at the app's runtime.

Cleo's stated requirement, asked directly and answered without hesitation: she wants to be able to choose and switch the runtime extraction LLM freely — not be locked into one provider or model.

## Decision

The ingestion/extraction pipeline calls the runtime LLM through an explicit provider abstraction. It never hardcodes a specific model or API call.

- A stable interface (e.g. an `extract(text, context) -> ExtractionResult` function/class) defines the contract every provider must satisfy — the input/output shape is independent of which model answers it.
- Concrete provider implementations (a local Ollama endpoint, the Anthropic API, the OpenAI API, others later) live behind that interface. Ingestion logic never imports or references a specific provider directly.
- The active provider is chosen via local configuration — per ADI-002/ADI-005's placement rule: local, per-device, never inside the Obsidian vault, never synced. A config file or environment variable, not a hardcoded value.
- Switching providers is a configuration change, not a code change to the ingestion pipeline itself.

This ADR decides the **architecture** (pluggable/swappable), not **which** provider ships as the default. The default is an implementation detail for the ingestion ticket itself, free to pick whatever's simplest to wire first (e.g. reusing an already-running local Ollama setup), without that choice locking anything in.

## Alternatives considered

- **Hardcode one provider** (e.g. always call a specific local model). Rejected: directly conflicts with Cleo's explicit requirement to choose and switch freely, and would force ingestion-logic changes every time she wants to try a different model.
- **Per-call provider selection** (choosing the model in each individual ingestion request, rather than a device-level default). Not rejected — worth allowing later as an additive refinement ("extract this one with model X") — but the config-level default is the necessary baseline for V1; per-call override can be layered on top without revisiting this decision.

## Consequences

- Whoever drafts and implements the ingestion ticket must design against the `extract()` interface, not any specific SDK or API — a concrete constraint on that ticket's scope.
- Each concrete provider brings its own setup (an API key for a cloud provider, a local endpoint URL for Ollama). This local configuration is out of scope for canonical/synced storage, consistent with ADI-002 and ADI-005.
- Output quality and consistency across providers is not guaranteed by this ADR — different models may extract somewhat differently from the same text. That is an accepted, expected trade-off of the flexibility Cleo asked for, not a defect to "fix" architecturally.
- A future ticket will need to define the first 1-2 concrete provider implementations and the config mechanism for selecting between them — not yet scoped, comes after the ingestion pipeline itself is cadré.
