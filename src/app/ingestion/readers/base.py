"""
Base interfaces for source readers used in ingestion.
"""
from typing import Protocol, Dict, Type
from pathlib import Path


class SourceReader(Protocol):
    """Interface for reading source files."""

    def read(self, path: Path) -> str:  # returns raw text content
        ...


class SourceReaderRegistry:
    """Registry mapping file extensions to SourceReader implementations."""

    def __init__(self):
        self._readers: Dict[str, Type[SourceReader]] = {}

    def register(self, extension: str, reader_class: Type[SourceReader]):
        """Register a reader for a specific file extension."""
        self._readers[extension] = reader_class

    def get_reader(self, extension: str) -> Type[SourceReader]:
        """Get the reader class for a given file extension."""
        return self._readers.get(extension)

    def read_file(self, path: Path) -> str:
        """Read content from a file using the appropriate reader."""
        extension = path.suffix.lower()
        reader_class = self.get_reader(extension)

        if not reader_class:
            raise ValueError(f"No reader registered for extension '{extension}'")

        reader = reader_class()
        return reader.read(path)