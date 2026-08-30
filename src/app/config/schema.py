"""
Typed schema for the Pekopeko local device configuration (ADI-008).
"""
from dataclasses import dataclass, field
from pathlib import Path


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
    index_dir: Path = field(default_factory=lambda: Path.home() / ".pekopeko" / "retrieval_index")


@dataclass
class TaskStateConfig:
    dir: Path = field(default_factory=lambda: Path.home() / ".pekopeko" / "task_state")


@dataclass
class DefaultConfig:
    """
    Reserved, not yet consumed by any pipeline - ingest_source()/extract_source()
    still require an explicit domain argument. Kept here only so a future
    ticket can wire it in without a schema change.
    """
    domain: str = "PERSONAL"


@dataclass
class PekopekoConfig:
    llm_provider: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    task_state: TaskStateConfig = field(default_factory=TaskStateConfig)
    default: DefaultConfig = field(default_factory=DefaultConfig)
