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

Configuration is handled through environment variables in `.env` file:

```env
# Ollama provider settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=60

# Vault root directory
VAULT_ROOT=./vault

# Task state directory
TASK_STATE_DIR=./task_state

# Default domain for ingestion
DEFAULT_DOMAIN=PERSONAL
```

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

### Testing

Tests use pytest with `tmp_path` for vault_root and task state directories to ensure no real files are touched.