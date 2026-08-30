# Pekopeko - Knowledge Core

## Data Ingestion Module (TASK-001)

This is the implementation of TASK-001: Data Ingestion Module (V1) for the Pekopeko project.

### Features Implemented

- **Markdown source file ingestion**: Reads Markdown files and preserves them as canonical source items
- **LLM-based assertion extraction**: Uses a pluggable provider interface to extract atomic knowledge assertions
- **Proposal creation**: Creates review-pending Proposal items from extracted assertions
- **Duplicate detection**: Detects exact duplicate re-ingestion by content hash
- **Atomic file writes**: Ensures all file operations are atomic using temporary files and `os.replace()`
- **Task state management**: Tracks ingestion attempts in local, non-canonical storage
- **Extensible architecture**: Supports adding new source formats and LLM providers

### Module Structure

```
app/
├── ingestion/
│   ├── __init__.py          # Main module exports
│   ├── pipeline.py          # Main ingestion orchestration
│   ├── storage.py           # Atomic write utilities and file handling
│   ├── task_state.py        # Task state management
│   ├── providers/
│   │   ├── __init__.py      # Provider exports
│   │   ├── base.py          # Base provider interface
│   │   └── ollama_provider.py # Ollama concrete implementation
│   └── readers/
│       ├── __init__.py      # Reader exports
│       ├── base.py          # Base reader interface
│       └── markdown_reader.py # Markdown reader implementation
```

### Configuration

Configuration is local to the device, never inside the vault (ADI-008), and
lives in a YAML file read by `app.config.load_config()`:

- **Location**: `~/.pekopeko/config.yaml` by default, overridable via the
  `PEKOPEKO_CONFIG_PATH` environment variable. A missing file is not an
  error - built-in defaults are used.
- **Schema**:
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
  ```
- **Environment-variable overrides** (bounded list, each overrides the
  corresponding file value for that one key): `PEKOPEKO_CONFIG_PATH`,
  `PEKOPEKO_LLM_PROVIDER`, `PEKOPEKO_OLLAMA_BASE_URL`, `PEKOPEKO_OLLAMA_MODEL`,
  `PEKOPEKO_OLLAMA_TIMEOUT`, `PEKOPEKO_TASK_STATE_DIR`,
  `PEKOPEKO_RETRIEVAL_INDEX_DIR`.
- **`.env` companion file** (optional, next to the resolved `config.yaml` -
  default `~/.pekopeko/.env`): loaded via `python-dotenv` for secrets/
  sensitive values, recognizing only the same bounded `PEKOPEKO_*` keys
  above - not a separate key namespace. A real process env var still wins
  over a `.env` value.
- **`default.domain`**: reserved for a future ticket, not yet read by
  `ingest_source`/`extract_source`.

`vault_root` remains an explicit caller-supplied parameter to
`ingest_source`/`extract_source` - it has no configuration surface (YAML or
`.env`).

### Usage

```python
from app.ingestion import ingest_source, OllamaProvider, OllamaProviderConfig
from pathlib import Path

# Configure provider
config = OllamaProviderConfig()
provider = OllamaProvider(config)

# Ingest a source file
result = ingest_source(
    vault_root=Path("./vault"),
    domain="PERSONAL",
    source_path=Path("./source.md"),
    provider=provider
)
```

### Compliance

This implementation complies with all relevant ADRs:
- ADI-001: Canonical persistence model (structured files, no git)
- ADI-004: Obsidian role (vault layout with domain folders)
- ADI-005: Sync vs async (async ingestion, task state outside vault)
- ADI-007: Implementation language (Python)
- ADI-008: LLM provider architecture (pluggable interface)

### Acceptance Criteria Met

1. ✓ Ingesting a .md source file produces Source and Proposal files with required frontmatter
2. ✓ No pipeline code imports concrete LLM SDKs directly
3. ✓ Duplicate ingestion detection works correctly
4. ✓ Error handling preserves data integrity
5. ✓ Extensibility for new readers supported
6. ✓ Extensibility for new providers supported
7. ✓ All assertions have valid epistemic_status
8. ✓ All writes are atomic
9. ✓ No git usage in implementation

### Dependencies

- Python 3.8+
- PyYAML (`pip install pyyaml`)
- requests (for Ollama provider, `pip install requests`)
- python-dotenv (for the optional `.env` config companion file, `pip install python-dotenv`)

### Testing

Tests use pytest with `tmp_path` for vault_root and task state directories to ensure no real files are touched.