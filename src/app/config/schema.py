"""
Typed schema for the Pekopeko local device configuration (ADI-008).
"""
from dataclasses import dataclass, field
from pathlib import Path

# src/app/config/schema.py -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class OllamaProviderSettings:
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout: int = 60
    temperature: float = 0.7


@dataclass
class LLMProviderConfig:
    active: str = "ollama"
    ollama: OllamaProviderSettings = field(default_factory=OllamaProviderSettings)


@dataclass
class RetrievalConfig:
    index_dir: Path = field(default_factory=lambda: _PROJECT_ROOT / ".pekopeko" / "retrieval_index")


@dataclass
class TaskStateConfig:
    dir: Path = field(default_factory=lambda: _PROJECT_ROOT / ".pekopeko" / "task_state")


@dataclass
class DefaultConfig:
    """
    Reserved, not yet consumed by any pipeline - ingest_source()/extract_source()
    still require an explicit domain argument. Kept here only so a future
    ticket can wire it in without a schema change.
    """
    domain: str = "PERSONAL"


@dataclass
class FolderWatchConfig:
    """ADI-013: background _inbox/ polling. File-only section (no PEKOPEKO_*
    env override, ADI-010's accepted asymmetry for options that don't need
    process-level override)."""
    enabled: bool = False
    poll_interval_seconds: int = 30
    inbox_dirname: str = "_inbox"
    processed_dirname: str = "processed"


@dataclass
class PekopekoConfig:
    llm_provider: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    task_state: TaskStateConfig = field(default_factory=TaskStateConfig)
    default: DefaultConfig = field(default_factory=DefaultConfig)
    folder_watch: FolderWatchConfig = field(default_factory=FolderWatchConfig)
