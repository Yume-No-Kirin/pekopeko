# ADI-011: Provider Zero-Output Contract

- **ID**: ADI-011
- **Date**: 2026-09-03
- **Status**: Accepted (confirmed by Cleo on 2026-09-03)

## Context

gpt-oss:20b ("thinking" model), used as the runtime extraction LLM behind a local Ollama
endpoint, exhausted its context window reasoning about a prompt and never produced a body:
Ollama returned `done_reason: "length"` with an empty `"response"` field. Neither concrete
`OllamaProvider` implementation (`ingestion/providers/ollama_provider.py`,
`extraction/providers/ollama_provider.py`) reads `done`/`done_reason` at all — both only do
`result_data.get("response", "")` and parse it. An empty response parses to an empty
assertion/entity/event/relationship list without raising, so `ingest_source()`/
`extract_source()` recorded the task as `status: "completed"` with 0 extracted items — a
silent success indistinguishable from "this source legitimately had nothing to extract."

Per ADI-008, the runtime extraction LLM is pluggable and provider-agnostic by design: the
pipeline never hardcodes a specific model or API. That means this exact failure mode —
empty or truncated output silently recorded as a normal completion — is not specific to
gpt-oss:20b or to Ollama; any current or future concrete `Provider` can produce empty
output (model refusal, truncation, a malformed prompt, an API-level partial response) and,
absent an explicit contract, the pipeline has no way to tell that apart from "nothing was
there to extract."

## Decision

The `Provider.extract()` contract (both `ingestion/providers/base.py` and
`extraction/providers/base.py`) requires:

- A call that produces zero extracted items for non-empty source content — zero assertions
  for `ingestion/`; zero entities, events, and relationships combined for `extraction/` —
  must raise. It must never return an empty-but-"successful" `ExtractionResult`.
- A source file that is itself empty or whitespace-only is handled separately, by a
  pipeline-level guard that runs *before* the provider is ever called. This keeps "the
  provider returned nothing for real content" and "there was nothing to give the provider"
  as two distinct, never-conflated failure conditions.
- Where the underlying LLM API exposes a machine-readable reason for an incomplete or
  truncated generation (Ollama's `done_reason` is the concrete example that motivated this
  ADR), the concrete provider should capture and surface it in the raised error's message,
  so the diagnostic reaches `task_state.error` instead of a bare "0 output" message. This is
  a "should" — best-effort, provider-specific — not a hard requirement for a provider whose
  API exposes no equivalent signal.

This ADR decides the **contract** every `Provider` implementation must honor, not how any
one concrete provider implements it — that is scoped to the implementing ticket (TASK-001c
for `OllamaProvider`).

## Alternatives considered

- **A new `TaskState.status` value** (e.g. `"failed_empty_output"`, distinct from
  `"failed"`). Rejected: no consumer needs a sixth state — the existing `"failed"` status
  plus a descriptive `error` string already satisfies "fail loudly, with a reason," and the
  frontend (`TaskStatusBadge.jsx`) already renders `"failed"` + `error` correctly. Adding a
  status would touch the frontend for no behavioral gain.
- **A pipeline-level check** after `provider.extract()` returns, instead of inside the
  provider itself (i.e. `ingest_source()`/`extract_source()` inspect the returned
  `ExtractionResult` and decide failure there). Rejected: duplicates the same check across
  two independent pipelines rather than once per provider, and loses the diagnostic
  (`done_reason` or equivalent) that is only available at the point the raw HTTP response is
  parsed — by the time a pipeline sees the returned `ExtractionResult`, that context is gone
  unless deliberately threaded through, which this alternative doesn't otherwise need.
  Raising from inside the provider also means the check travels automatically to any future
  caller of a `Provider` directly (a test, a future CLI), not just the two pipeline
  functions.
- **Automatic retry on empty/truncated output** (re-issue the call once before giving up).
  Out of scope for this ADR: no retry/backoff convention exists anywhere in this codebase
  today (confirmed absent in both `OllamaProvider` implementations, which wrap any exception
  into a single generic message with no retry). Introducing retry semantics is a separate,
  unrelated architectural decision — this ADR only decides that empty output is a *failure*,
  not what should automatically happen in response to that failure.

## Consequences

- Both concrete `OllamaProvider` implementations need a code change to raise on zero output
  and to add the empty-source pipeline guard — ticketed separately as TASK-001c so this ADR
  states the contract and the ticket implements it.
- A future second `Provider` implementation (noted as TASK-020 in TASK-001a's Out of scope,
  not yet ticketed) inherits this contract automatically: it must raise on zero output for
  non-empty input, and may optionally surface its own truncation/failure reason if its API
  exposes one.
- No change to the existing `"failed"` `TaskState.status` shape, to `IngestionResult`/
  `ExtractionPipelineResult`, or to any frontend rendering of task failure — the fix is
  entirely about *when* a failure is raised, not a new failure *shape*.
- Empty-source detection becomes new, explicit pipeline-level behavior: previously an empty
  source file would reach the provider and, per this same class of bug, could silently
  succeed with 0 assertions; going forward it is caught earlier with its own distinct error
  message, never confused with "the provider returned nothing for real content."
