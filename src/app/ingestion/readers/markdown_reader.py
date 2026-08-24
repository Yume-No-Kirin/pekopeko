"""
Markdown source reader implementation.
"""
from pathlib import Path
from .base import SourceReader


class MarkdownReader(SourceReader):
    """Concrete implementation of SourceReader for Markdown files."""

    def read(self, path: Path) -> str:
        """
        Read a markdown file and return its content.

        Args:
            path: Path to the markdown file

        Returns:
            The raw text content of the file
        """
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()