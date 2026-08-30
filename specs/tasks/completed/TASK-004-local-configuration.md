# TASK-004: Local Configuration Mechanism (V1)

- **Status**: completed

## Objective

Implement a single local configuration mechanism that TASK-001 and TASK-003 already assume exists (ADI-008: "the active provider is chosen via local configuration") without ever formalizing it. Concretely: a YAML config file (plus a bounded set of environment-variable overrides), local to the device, never inside the vault, that governs (1) which concrete LLM provider is active and its settings, (2) where the (not-yet-built) retrieval index should live, and (3) where async task-state files should live. Wire this minimally into `ingestion/pipeline.py` and `extraction/pipeline.py` so the gap is actually closed, not just documented by an unused module.

This ticket does not add any new capability to ingestion or extraction beyond configuration plumbing — no new extraction logic, no new file types, no review/canonical changes.

## Binding context (references, not duplicated here)

- ADI-002 (retrieval-system, Accepted): the retrieval index is a derived, rebuildable, local, per-device index, never stored inside the Obsidian vault. This ticket only reserves the config key for where that index will live (`retrieval.index_dir`) — no retrieval code exists yet to consume it (future TASK-007).
- ADI-005 (sync-vs-async, Accepted): in-flight async task state is persisted locally, outside the vault, per-device, not synced, not canonical. This ticket's `task_state.dir` key is exactly that placement, made configurable instead of hardcoded per pipeline.
- ADI-008 (llm-provider-architecture, Accepted): the ingestion/extraction pipelines call the runtime LLM through a provider abstraction; the active provider is chosen via local configuration (a config file or environment variable), never hardcoded; switching providers is a configuration change, not a pipeline code change. This ADR is the direct driver of this ticket.
- ADI-007 (implementation-language, Accepted): Python.
- Module independence discipline established by TASK-002/TASK-003 (`review/` never imports `ingestion/`; `extraction/` never imports `ingestion/` or `review/` — only the on-disk frontmatter contract is shared): `app/config` must never import `app.ingestion`, `app.extraction`, or `app.review`. It is a new, neutral, dependency-free module; pipelines may depend on it, never the reverse.
- `specs/tasks/completed/TASK-001-data-ingestion.md` and `specs/tasks/completed/TASK-003-entity-event-relationship-extraction.md`: both currently hardcode a task-state default (`Path.home() / ".pekopeko" / "ingestion_state"` and `.../ "extraction_state"` respectively) and require the caller to construct a `Provider` instance by hand — this ticket makes the task-state default config-driven and adds an opt-in provider-construction helper per pipeline, without changing either pipeline function's signature.

## Scope

Implement a Python package providing:

1. A YAML configuration file, local to the device, never committed to the vault, with a documented schema covering LLM provider selection, retrieval index location, and task-state location.
2. A loader that resolves the file's location, applies a bounded set of environment-variable overrides, validates the result, and returns built-in defaults when no file is present — never raising just because the file is missing.
3. A typed validation error when a present file is malformed or a value is out of schema — never a silent fallback for a value that *is* present but invalid.
4. A small, optional provider-construction helper in each of `ingestion/` and `extraction/` that turns a loaded config into a concrete `Provider` instance for that pipeline — used by callers, never by `pipeline.py` itself.
5. A minimal edit to `ingestion/pipeline.py` and `extraction/pipeline.py` so their existing (optional) `state_dir` parameter defaults to a config-derived path instead of a hardcoded literal, when the caller doesn't pass one explicitly.

### V1 scope decisions

- **Primary config file format: YAML.** For configuration paths, names, and variables — see "Config schema (exact contract)" below.
- **Companion secrets file format: `.env` (amendment, 2026-08-30).** Optional, next to the resolved `config.yaml`, loaded via `python-dotenv`. It is *not* a second key namespace — it only recognizes the same bounded `PEKOPEKO_*` keys as the env-var overrides below, loaded into `os.environ` (a real process env var still wins over a `.env` value). See "`.env` example" below.
- **YAML Config file location**: `~/.pekopeko/config.yaml` by default (same `Path.home() / ".pekopeko"` convention already used by `ingestion/task_state.py`'s and `extraction/pipeline.py`'s own hardcoded defaults), overridable via `PEKOPEKO_CONFIG_PATH`.
- **Missing YAML file is not an error** — `load_config()` returns full built-in defaults. This applies even when `PEKOPEKO_CONFIG_PATH` points at a path that doesn't exist (treated the same as "no file", not a hard failure), so a fresh device with no config works out of the box.
- **Malformed content is an error.** Invalid YAML syntax, or a present value that fails schema validation (unknown provider name, non-numeric timeout, etc.), raises a typed `ConfigError` before returning — never silently ignored or defaulted.
- **Environment-variable overrides are a bounded, explicit list** — not a generic arbitrary-key override mechanism: `PEKOPEKO_CONFIG_PATH`, `PEKOPEKO_LLM_PROVIDER`, `PEKOPEKO_OLLAMA_BASE_URL`, `PEKOPEKO_OLLAMA_MODEL`, `PEKOPEKO_OLLAMA_TIMEOUT`, `PEKOPEKO_TASK_STATE_DIR`, `PEKOPEKO_RETRIEVAL_INDEX_DIR`. When set, an env var overrides the corresponding file value (or default) for that one key only.
- **Provider selection stays a two-step, explicit process.** `load_config()` never returns a `Provider` instance itself (it has no knowledge of the `Provider` protocol, to avoid `app/config` depending on `app.ingestion`/`app.extraction`). Each pipeline's own `providers/factory.py` maps config values to that pipeline's own concrete provider class. `ingest_source()`/`extract_source()` keep `provider` as a required parameter with no default — the factory is a convenience for callers, never invoked implicitly by the pipeline.
- **Only the `ollama` branch is required for V1** in each factory — matches the one concrete provider TASK-001/003 already ship. The schema/factory shape must make adding a second provider (TASK-020) a matter of adding a sub-section plus a branch, not a redesign, but that second provider is not built here.
- **`task_state.dir` is a single root**, with each pipeline resolving its own subfolder (`<task_state.dir>/ingestion`, `<task_state.dir>/extraction`) — replacing the two independently-hardcoded literals that exist today.

### YAML Config schema (exact contract)

```yaml
llm_provider:
  active: ollama          # which concrete provider is active
  ollama:
    base_url: http://localhost:11434
    model: llama3
    timeout: 60
retrieval:
  index_dir: ~/.pekopeko/retrieval_index
task_state:
  dir: ~/.pekopeko/task_state
default:
  domain: PERSONAL        # reserved - not read by ingest_source()/extract_source() (see Out of scope)
```

### .env example (amendment, 2026-08-30)

A companion `.env` file, next to the resolved `config.yaml` (default
`~/.pekopeko/.env`), for secrets/sensitive values. It is loaded via
`python-dotenv` and only recognizes the same 7 bounded `PEKOPEKO_*` keys
already listed above under "Environment-variable overrides" — it is not a
second, separately-named key namespace, and a real process env var still
wins over a `.env` value:

```env
# ~/.pekopeko/.env - optional, never committed, same bounded keys as above
PEKOPEKO_OLLAMA_BASE_URL=http://localhost:11434
PEKOPEKO_OLLAMA_MODEL=llama3
```

`vault_root` has no config surface at all (YAML or `.env`) — it remains a
caller-supplied parameter, per "Out of scope" below.

Loaded into typed dataclasses in `app/config/schema.py`:

```python
@dataclass
class OllamaProviderSettings:
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout: int = 60

@dataclass
class LLMProviderConfig:
    active: str = "ollama"
    ollama: OllamaProviderSettings = field(default_factory=OllamaProviderSettings)

@dataclass
class RetrievalConfig:
    index_dir: Path = Path.home() / ".pekopeko" / "retrieval_index"

@dataclass
class TaskStateConfig:
    dir: Path = Path.home() / ".pekopeko" / "task_state"

@dataclass
class PekopekoConfig:
    llm_provider: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    task_state: TaskStateConfig = field(default_factory=TaskStateConfig)
```

### Loader interface

```python
def load_config(path: Optional[Path] = None) -> PekopekoConfig: ...
```

Resolution order: explicit `path` argument > `PEKOPEKO_CONFIG_PATH` env var > default `~/.pekopeko/config.yaml`. After the file (if any) is parsed, the bounded env-var list is applied on top, per-key. Result is validated (unknown `llm_provider.active`, non-numeric `timeout`, etc. raise `ConfigError`) before being returned.

### Provider factory interface (per pipeline)

```python
# ingestion/providers/factory.py
def build_configured_provider(cfg: PekopekoConfig) -> Provider: ...

# extraction/providers/factory.py
def build_configured_provider(cfg: PekopekoConfig) -> Provider: ...
```

Each raises a typed error (not a silent default to `ollama`) if `cfg.llm_provider.active` names a provider that module doesn't implement.

## Requirements

- Python only (ADI-007). `pyyaml` for parsing the config file — already pinned in `src/requirements.txt`. `python-dotenv` for the companion `.env` file (amendment, 2026-08-30) — newly pinned in `src/requirements.txt`.
- All directory creation implied by `retrieval.index_dir` / `task_state.dir` defaults happens lazily wherever those paths are actually used (this ticket only resolves the paths; it does not need to create them itself since nothing in-scope writes there yet beyond what `ingest_source`/`extract_source` already do for task state).
- No use of git anywhere in the implementation (ADI-001).
- `app/config` has no dependency on `app.ingestion`, `app.extraction`, or `app.review`.

## Constraints

- No new third-party dependency beyond the already-pinned `pyyaml` and (amendment, 2026-08-30) `python-dotenv`.
- No database of any kind — the config file is plain YAML.
- No change to the public signature of `ingest_source()` or `extract_source()` — only the internal default-resolution of `state_dir` changes; `provider` remains a required parameter with no default.
- No generic/arbitrary environment-variable override mechanism — only the bounded, explicitly-named list above.
- No CLI or GUI for editing configuration — a hand-edited YAML file is sufficient for V1.
- No second concrete LLM provider (Anthropic/OpenAI, etc.) — future ticket (TASK-020, `specs/tasks/BACKLOG-CLAUDE.md`).
- No changes to `review/` — it has no LLM provider and no asynchronous task state (ADI-005 rule 3: accept/reject is synchronous), so nothing in this ticket applies to it.
- No consumption of `retrieval.index_dir` by any actual retrieval code — that key is reserved for future TASK-007, not implemented here.

## Files/modules concerned

- `app/config/__init__.py` — module exports.
- `app/config/errors.py` — `ConfigError`.
- `app/config/schema.py` — `OllamaProviderSettings`, `LLMProviderConfig`, `RetrievalConfig`, `TaskStateConfig`, `DefaultConfig` (amendment, 2026-08-30), `PekopekoConfig`.
- `app/config/loader.py` — `load_config()`, file-location resolution, `.env` loading (amendment, 2026-08-30), env-var overrides, validation.
- `app/ingestion/providers/factory.py` — new, `build_configured_provider(cfg) -> Provider` for ingestion's own `Provider`/`OllamaProvider`.
- `app/extraction/providers/factory.py` — new, `build_configured_provider(cfg) -> Provider` for extraction's own `Provider`/`OllamaProvider`.
- `app/ingestion/pipeline.py` — targeted edit: replace the hardcoded `state_dir` fallback literal with `load_config().task_state.dir / "ingestion"`.
- `app/extraction/pipeline.py` — targeted edit: replace the module-level `DEFAULT_STATE_DIR` constant with an equivalent computed at call time inside `extract_source()` (`load_config().task_state.dir / "extraction"`), so config is read fresh rather than baked in at import.
- `src/README.md` — correct the existing "Configuration" section (currently describes an unimplemented `.env` pattern) to describe the real YAML mechanism delivered here.
- `tests/config/` — new, mirroring `app/config/`. Amendment, 2026-08-30: `tests/config/test_dotenv.py` (new), `tests/config/test_loader_file_override.py` (2 tests added for `default.domain`).
- `tests/ingestion/` and `tests/extraction/` — a small number of *additional* tests for the new default-resolution behavior; no rewrite of existing tests.
- `src/requirements.txt` — amendment, 2026-08-30: `python-dotenv>=1.0.0` added.

## Dependencies

None beyond what already exists (`app.ingestion`, `app.extraction` as edit targets — their public interfaces are unchanged, only internal defaults). `app/config` itself has no dependencies on other project modules. Amendment, 2026-08-30: `app/config/loader.py` depends on the newly-pinned `python-dotenv`.

## Acceptance criteria

1. With no config file present and no relevant environment variable set, `load_config()` returns a `PekopekoConfig` with the documented built-in defaults (`ollama` / `~/.pekopeko/retrieval_index` / `~/.pekopeko/task_state`) and never raises.
2. A YAML file that sets only a subset of keys applies a partial override — keys absent from the file keep their built-in default (verified for at least one key per top-level section).
3. Setting `PEKOPEKO_CONFIG_PATH` makes `load_config()` read from that exact path instead of the default `~/.pekopeko/config.yaml`; a missing file at that explicit path is treated as "no file" (defaults), not an error.
4. A malformed YAML file, or a present-but-invalid value (unknown `llm_provider.active`, non-numeric `timeout`), raises a typed `ConfigError` before `load_config()` returns — never a silent fallback to a default for a value that was actually present.
5. Each environment-variable override in the bounded list takes precedence over the corresponding file value when both are set (at least one test per top-level config section: provider, retrieval, task_state).
6. `ingestion.providers.factory.build_configured_provider` and `extraction.providers.factory.build_configured_provider`, given a config with `llm_provider.active == "ollama"`, each return an instance of that module's own `OllamaProvider`, constructed with the config's `base_url`/`model`/`timeout` — verified without any real network call.
7. Given an unknown `llm_provider.active` value, both factories raise a typed error rather than silently defaulting to `ollama`.
8. Calling `ingest_source(...)` / `extract_source(...)` without an explicit `state_dir` resolves the task-state directory from config (`<task_state.dir>/ingestion` and `<task_state.dir>/extraction` respectively) instead of the previous hardcoded literals — verified by pointing `PEKOPEKO_CONFIG_PATH` or `PEKOPEKO_TASK_STATE_DIR` at a `tmp_path` fixture, never touching a real `~/.pekopeko`.
9. `app/config` never imports `app.ingestion`, `app.extraction`, or `app.review` — verifiable by static inspection (same pattern as TASK-001 AC2 / TASK-003's import-isolation tests).
10. No default value anywhere in the schema resolves to a path inside a vault — all defaults are under `Path.home() / ".pekopeko"`, never relative to a `vault_root`.
11. Neither `ingest_source()` nor `extract_source()` changed its public parameter list — a caller passing all arguments exactly as before (including an explicit `provider` and `state_dir`) sees unchanged behavior.
12. **(amendment, 2026-08-30)** A companion `.env` file next to the resolved `config.yaml`, setting one of the bounded `PEKOPEKO_*` keys, applies exactly as if that key were set as a real process environment variable; a real process env var for the same key still wins over the `.env` value; a missing `.env` file is not an error.
13. **(amendment, 2026-08-30)** `default.domain` round-trips through YAML partial-override like the other schema sections (absent → `"PERSONAL"`; present → the file's value) but is never read by `ingest_source()` or `extract_source()` — no signature change, no behavior change to either function.

## Testing requirements

`pytest` unit tests covering every acceptance criterion above. Use `tmp_path` for any config file created in a test, and `monkeypatch` for environment variables — tests must never read or write a real `~/.pekopeko` directory. Provider factories must be tested without any real network call (the underlying `OllamaProvider` is only constructed, never invoked). Include at least:
- A no-file/no-env defaults test (Criterion 1).
- A partial-override-from-file test per schema section (Criterion 2).
- A `PEKOPEKO_CONFIG_PATH` resolution test, including the explicit-path-but-missing-file case (Criterion 3).
- A malformed-YAML test and an invalid-value test, both asserting `ConfigError` (Criterion 4).
- One environment-variable-override test per schema section (Criterion 5).
- A provider-factory construction test for each of `ingestion` and `extraction` (Criterion 6).
- An unknown-provider-name test for each factory (Criterion 7).
- A default-`state_dir`-resolution test for each of `ingest_source` and `extract_source`, isolated via `tmp_path` + env override (Criterion 8).
- A static-inspection/import-graph test for `app/config`'s independence (Criterion 9).
- A signature-stability test (or code-review-level confirmation) that existing callers passing explicit `provider`/`state_dir` are unaffected (Criterion 11).
- **(amendment, 2026-08-30)** A `.env`-value-applied test, a real-env-wins-over-.env test, and a missing-.env-is-not-an-error test (Criterion 12).
- **(amendment, 2026-08-30)** A `default.domain` partial-override test and an absent-default-domain test (Criterion 13).

Project-wide coverage discipline applies: ≥80% line coverage of `app/config` and of the touched portions of `app/ingestion`/`app/extraction`.

## Out of scope

- Actual consumption of `retrieval.index_dir` by a retrieval/search implementation — reserved for future TASK-007.
- A second concrete LLM provider (Anthropic, OpenAI, etc.) — future TASK-020; only the `ollama` branch is required here.
- Per-call provider override (choosing a model for one specific ingestion/extraction call rather than the device-level default) — an alternative ADI-008 explicitly did not reject but deferred; not built here.
- `vault_root` as a configuration value — despite being mentioned in `src/README.md`'s old aspirational "Configuration" section, it remains an explicit caller-supplied parameter to `ingest_source`/`extract_source`; no schema field, YAML or `.env`, exists for it.
- **`default.domain`** (amendment, 2026-08-30) is a *reserved, unconsumed* schema field — mirroring how `retrieval.index_dir` is reserved for future TASK-007. It round-trips through YAML partial-override like the other sections, but `ingest_source()`/`extract_source()` never read it; `domain` stays a required, explicit caller-supplied parameter with no signature change, same as before this amendment.
- Any CLI or GUI for creating/editing the config file.
- Any change to `review/` (`app.review`) — out of scope per ADI-005 rule 3 (no LLM provider, no asynchronous task state there).
- Consolidating `ingestion/providers/` and `extraction/providers/` code (duplication between their respective `OllamaProvider`/`OllamaProviderConfig` classes is pre-existing and deliberate, per TASK-003's notes) — future TASK-033, not this ticket.

## Verification record (2026-08-30)

Implemented by Claude (this session). Per this project's verification
discipline: code (`src/app/config/`, `src/app/ingestion/`, `src/app/extraction/`,
`src/tests/config/`, `src/tests/ingestion/`, `src/tests/extraction/`) was
copied to an isolated scratch directory (outside the repo,
`.../scratchpad/task004_verify/`) and the test suites re-run independently
there, rather than trusting the in-repo run alone. A hand-written manual
reproduction script (`manual_repro.py`, run in the isolated copy) exercised
`load_config()` defaults/override/error paths, both pipelines' provider
factories, and both pipelines' default `state_dir` resolution end-to-end,
printing every intermediate value for by-eye inspection. Each acceptance
criterion checked individually:

- `[PASS]` AC1 (no file, no env -> full built-in defaults, never raises) --
  `test_defaults_when_no_file_and_no_env` (`tests/config/test_loader_defaults.py`)
  passes in both runs; step 1 of `manual_repro.py` printed the returned
  `PekopekoConfig` and confirmed every field matches the documented default.
- `[PASS]` AC2 (partial YAML file overrides only the keys it sets) --
  one test per section in `tests/config/test_loader_file_override.py`
  (`llm_provider.ollama.model`, `retrieval.index_dir`, `task_state.dir`) all
  pass in both runs; step 2 of `manual_repro.py` confirmed a file setting
  only `model` left `base_url`/`timeout` at their defaults.
- `[PASS]` AC3 (`PEKOPEKO_CONFIG_PATH` resolution, including missing-file-at-
  explicit-path treated as "no file") --
  `tests/config/test_loader_path_resolution.py` (4 tests: default path used
  when no explicit path/env var is given, env-path used, missing file at env
  path is not an error, explicit `path` arg wins over the env var) pass in
  both runs.
- `[PASS]` AC4 (malformed YAML or invalid present value raises `ConfigError`,
  never a silent fallback) -- `tests/config/test_loader_errors.py` (7 tests:
  malformed YAML, unknown `llm_provider.active` from file, non-numeric
  `timeout` from file, unknown `llm_provider.active` from env var,
  non-numeric `timeout` from env var, empty YAML file treated as no
  overrides, non-mapping top-level YAML raises) all pass in both runs; step
  3 of `manual_repro.py` confirmed the exact `ConfigError` message for an
  unknown provider value.
- `[PASS]` AC5 (each bounded env var overrides its file counterpart) --
  `tests/config/test_loader_env_overrides.py`, one test per section
  (provider, including `PEKOPEKO_LLM_PROVIDER` itself plus
  `PEKOPEKO_OLLAMA_*`; `PEKOPEKO_RETRIEVAL_INDEX_DIR`;
  `PEKOPEKO_TASK_STATE_DIR`), all pass in both runs.
- `[PASS]` AC6 (`build_configured_provider` with `active=="ollama"` returns
  that module's own `OllamaProvider`, constructed from the config's
  `base_url`/`model`/`timeout`, no network call) --
  `test_build_configured_provider_returns_ollama_provider` in both
  `tests/ingestion/test_provider_factory.py` and
  `tests/extraction/test_provider_factory.py` pass in both runs; steps 4-5 of
  `manual_repro.py` printed the constructed provider's type and model for
  both pipelines.
- `[PASS]` AC7 (unknown `llm_provider.active` raises a typed error, no silent
  `ollama` fallback) -- `test_build_configured_provider_raises_on_unknown_provider`
  in both factory test files pass in both runs; step 6 of `manual_repro.py`
  confirmed the raised `ConfigError` message for the ingestion factory.
- `[PASS]` AC8 (`ingest_source()`/`extract_source()` without an explicit
  `state_dir` resolve `<task_state.dir>/ingestion` and
  `<task_state.dir>/extraction` respectively from config) --
  `test_default_state_dir_resolved_from_env_config`
  (`tests/ingestion/test_config_integration.py`, new) and
  `test_default_state_dir_used_when_not_provided`
  (`tests/extraction/test_pipeline.py`, updated from the removed
  `DEFAULT_STATE_DIR` monkeypatch to `PEKOPEKO_TASK_STATE_DIR`) both pass in
  both runs; steps 7-8 of `manual_repro.py` confirmed the on-disk task-state
  file landed under `<PEKOPEKO_TASK_STATE_DIR>/ingestion` and
  `<PEKOPEKO_TASK_STATE_DIR>/extraction` respectively, in an isolated
  `tmp_path`/temp dir, never touching a real `~/.pekopeko`.
- `[PASS]` AC9 (`app/config` never imports `app.ingestion`, `app.extraction`,
  or `app.review`) -- `test_config_module_does_not_import_other_app_modules`
  (`tests/config/test_import_isolation.py`) passes in both runs; step 9 of
  `manual_repro.py` re-confirmed by an independent grep-style scan; a manual
  `grep -rn "ingestion\|extraction\|review" src/app/config/` on the real
  working tree also returns nothing.
- `[PASS]` AC10 (no schema default resolves inside a vault; all defaults are
  under `Path.home() / ".pekopeko"`) -- confirmed by reading
  `src/app/config/schema.py` (`RetrievalConfig`/`TaskStateConfig` defaults
  are both `Path.home() / ".pekopeko" / ...`, no `vault_root` reference
  anywhere in `app/config`); step 1 of `manual_repro.py`'s printed output
  shows both resolving under the real `~/.pekopeko`.
- `[PASS]` AC11 (neither `ingest_source()` nor `extract_source()` changed its
  public parameter list) -- `test_ingest_source_signature_is_unchanged` and
  `test_extract_source_signature_is_unchanged` (`inspect.signature`, in both
  `test_provider_factory.py` files) pass in both runs; additionally, every
  pre-existing test in `tests/ingestion/` and `tests/extraction/` that calls
  `ingest_source`/`extract_source` with explicit `provider`/`state_dir`
  continues to pass unmodified (only one pre-existing test,
  `test_default_state_dir_used_when_not_provided`, needed updating, because
  it exercised the *old* hardcoded-default mechanism this ticket explicitly
  replaces, not because the signature changed).
- `[PASS]` Test coverage -- `pytest --cov=src.app.config` reports **100%**
  line coverage (102/102 statements across `__init__.py`/`errors.py`/
  `loader.py`/`schema.py`) in both the working tree and the isolated copy
  (the initial pass was 94%, 96/102; 5 targeted tests were added to close
  the gaps: default-path resolution with no explicit path/env var, an
  invalid `PEKOPEKO_LLM_PROVIDER` value, an invalid `PEKOPEKO_OLLAMA_TIMEOUT`
  value, an empty YAML file, and a non-mapping top-level YAML value).
  Touched portions of `app/ingestion`/`app/extraction`: both new
  `providers/factory.py` files are 100% covered; `extraction/pipeline.py`
  stays 100%; `ingestion/pipeline.py` stays at its pre-existing 82% (the
  uncovered lines are pre-existing error-handling paths this ticket did not
  touch). All figures identical between the working tree and the isolated
  copy. Project requirement (>=80%) met and exceeded for `app/config` and
  for the touched code.
- `[PASS]` 19/19 `tests/config/` tests pass in the working tree and again,
  independently, in an isolated scratch copy. `tests/ingestion/` and
  `tests/extraction/` each pass identically in both locations: 29/31
  (ingestion, 2 failures pre-existing and unrelated to this ticket -- see
  below) and 44/44 (extraction).
- `[NOT RUN]` Real Ollama endpoint / GUI interaction -- not applicable
  (`OllamaProvider` is only constructed by the factories, never invoked, per
  the project's "no real network calls" testing rule; ticket has no GUI/CLI
  requirement).

**Pre-existing failures, confirmed unrelated to this ticket**: two tests in
`tests/ingestion/` fail both before and after this ticket's changes --
`test_comprehensive.py::test_acceptance_criteria_compliance` and
`test_pipeline.py::test_import_isolation` -- both read a source file via a
hardcoded path relative to the working directory
(`Path("app/ingestion/pipeline.py")` instead of
`Path("src/app/ingestion/pipeline.py")`) and fail with `FileNotFoundError`
regardless of this ticket. Left untouched per this ticket's scope (no
unrelated cleanup).

**Honesty note on independence**: this verification was performed by the same
Claude session that wrote the implementation, not by a separate reviewer or
model (same caveat flagged in TASK-002's and TASK-003's verification
records). It does follow the isolated-copy-and-independently-rerun
discipline the project asks for, plus a manual by-eye script beyond just
re-running pytest, but it is not the same strength of evidence as an
independent second reviewer.

## Amendment verification (2026-08-30)

Cleo hand-edited this ticket after the original implementation/verification
above to add `.env` secrets support and a reserved `default.domain` schema
field. Three clarifying questions were asked and answered (recorded in the
"V1 scope decisions" / ".env example" / "Out of scope" sections above) before
implementing. Same isolated-copy discipline as the original record:

- `[PASS]` AC12 (`.env` value applies as a bounded override; real env var
  wins over `.env`; missing `.env` is not an error) --
  `tests/config/test_dotenv.py` (3 tests) pass in both the working tree and
  an isolated scratch copy; manual steps 1-3 of `manual_repro_dotenv.py`
  printed and confirmed each case by eye. The test file uses an autouse
  fixture to snapshot/restore the full `os.environ` around each test, since
  `python-dotenv` writes directly into `os.environ` (bypassing
  `monkeypatch`'s undo tracking) and would otherwise leak `PEKOPEKO_*`
  values into later tests in the same pytest process.
- `[PASS]` AC13 (`default.domain` partial-override round-trip, never read by
  either pipeline) -- `test_partial_override_default_domain` and
  `test_default_domain_falls_back_when_absent`
  (`tests/config/test_loader_file_override.py`) pass in both locations;
  manual step 4 of `manual_repro_dotenv.py` confirmed both the present and
  absent cases by eye. Confirmed by reading `src/app/ingestion/pipeline.py`
  and `src/app/extraction/pipeline.py`: neither references `cfg.default` or
  `.domain` anywhere -- purely reserved, no signature change.
- `[PASS]` Test coverage -- `pytest --cov=src.app.config` reports **100%**
  line coverage (113/113 statements, up from 102 -- `loader.py` grew from 75
  to 82 statements for the `.env`-loading step and the `default` section
  parse, `schema.py` grew from 22 to 26 for `DefaultConfig`) in both the
  working tree and the isolated copy.
- `[PASS]` 24/24 `tests/config/` tests pass (19 original + 5 new: 3 in
  `test_dotenv.py`, 2 in `test_loader_file_override.py`) in the working tree
  and again, independently, in an isolated scratch copy.
- `[PASS]` No regression -- `tests/ingestion/` (29/31, same 2 pre-existing
  unrelated failures as the original record) and `tests/extraction/` (44/44)
  pass identically in both locations; neither pipeline was touched by this
  amendment.
- `[PASS]` Dependency constraint -- `python-dotenv>=1.0.0` added to
  `src/requirements.txt` (already installed in this environment, v1.2.2);
  the ticket's "Constraints" section was updated to name it explicitly
  rather than silently contradicting the original "no new dependency beyond
  pyyaml" wording.
- `[PASS]` Internal consistency of the hand-edited sections -- the
  contradictions introduced by the manual edit (bare `OLLAMA_BASE_URL`/
  `VAULT_ROOT` keys in the `.env example` not matching the bounded
  `PEKOPEKO_*` list; `base_url` dropped from the YAML schema block despite
  staying in the dataclass; "Out of scope" still flatly forbidding
  `default.domain` as a config value) were resolved per Cleo's answers and
  fixed directly in the sections above -- `base_url` restored to the YAML
  block, the `.env example` rewritten to use real `PEKOPEKO_*` keys,
  `vault_root` confirmed to have no schema field anywhere (YAML or `.env`).

Same honesty note as above: this amendment's verification was performed by
the same Claude session that implemented it.

## Code-review triage (2026-08-30)

A code review submitted 9 numbered "anomalies" against `app/config`. Each
was checked directly against the code (reasoning plus throwaway,
non-mutating `python -c` repro snippets in a tempdir) before any fix was
made -- most did not hold up.

**Confirmed real, fixed:**

- `[FIXED]` Malformed nested YAML section (e.g. `llm_provider: 5`, a scalar
  where a mapping is expected) crashed with an unhandled `AttributeError`
  instead of raising `ConfigError` -- reproduced before the fix, confirmed
  raising `ConfigError` after. `loader.py` now has a `_require_mapping()`
  helper used for all 5 nested sections (`llm_provider`,
  `llm_provider.ollama`, `retrieval`, `task_state`, `default`). Tests:
  `test_non_mapping_nested_section_raises_config_error` (parametrized, 5
  cases) in `test_loader_errors.py`.
- `[FIXED]` No range validation on `timeout` -- a negative or zero value
  loaded successfully (reproduced: `timeout: -5` accepted before the fix).
  `_validate_timeout()`/`_validate_timeout_str()` now reject `<= 0`. Tests:
  `test_negative_timeout_from_file_raises_config_error`,
  `test_zero_timeout_from_file_raises_config_error`,
  `test_negative_timeout_via_env_var_raises_config_error`.
- `[FIXED]` An empty-string bounded env var (e.g.
  `PEKOPEKO_TASK_STATE_DIR=""`) silently resolved to `Path("")` (the cwd)
  instead of falling back to the file/default value (reproduced before the
  fix). `_apply_env_overrides()` now uses a truthy check
  (`env.get(KEY)`) for all 6 remaining bounded vars, matching the pattern
  `_resolve_path()` already used for `PEKOPEKO_CONFIG_PATH`. Test:
  `test_empty_string_env_var_is_treated_as_unset`.

**Checked and declined (not real, or already out of scope):**

- `[DECLINED]` "Timeout env-var type inconsistency" -- misreads the code;
  `_validate_timeout_str()` already converts the env-var string to `int`
  before assignment to the `int`-typed field. Nothing to fix.
- `[DECLINED]` "Race condition with concurrent dotenv/config access" -- not
  applicable to this project's local, single-device, single-process usage
  (ADI-002/ADI-005); no shared multi-process daemon reads/writes the config
  concurrently.
- `[DECLINED]` "Hardcoded `VALID_PROVIDERS = {'ollama'}`" -- explicit,
  documented V1 scope (Constraints: "No second concrete LLM provider...
  future ticket TASK-020"; AC7 requires exactly this rejection behavior),
  not an oversight.
- `[DECLINED]` "Memory leak in YAML loading" -- not a real concern;
  `yaml.safe_load()` on an in-memory string holds no open file handle and
  is normal GC-managed Python.
- `[DECLINED]` "Inconsistent use of `field(default_factory=...)`" --
  deliberate: `default_factory` is used specifically where `Path.home()`
  must be re-evaluated fresh per instantiation (verified by
  `test_default_path_used_when_no_arg_and_no_env_var`, which monkeypatches
  `Path.home()`); plain literal defaults are used where there's no such
  freshness concern. Not an inconsistency.
- `[DECLINED]` "Missing tests for empty/partial/invalid-YAML configs" --
  mostly already false: `test_empty_yaml_file_is_treated_as_no_overrides`,
  `test_malformed_yaml_raises_config_error`,
  `test_non_mapping_top_level_yaml_raises_config_error`, and the
  `test_loader_file_override.py` partial-override tests already existed.
  The one genuine gap (timeout range) is covered by the fixes above.

**Result**: `tests/config/` grew from 24 to 33 tests, all passing, 100% line
coverage maintained (`loader.py` grew from 82 to 94 statements). Verified
independently in an isolated scratch copy (same discipline as the rest of
this record) -- both original bug repros now raise `ConfigError` there too.
`tests/ingestion/` (29/31, same 2 pre-existing unrelated failures) and
`tests/extraction/` (44/44) unaffected in both locations.
