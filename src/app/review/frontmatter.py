"""
YAML frontmatter parsing and serialization.

Pure string transformation, no filesystem access - independently testable.
review/ has no dependency on ingestion/, so this reimplements frontmatter
handling rather than importing app.ingestion.storage.
"""
from typing import Any

import yaml

from .errors import ValidationError

# Files are always written as "---\n" + <yaml block ending in "\n"> + "---\n\n" + body
# (matches app/ingestion/storage.py's exact format). The closing sequence is
# therefore the yaml block's trailing newline, the closing "---" line, and the
# blank line separating frontmatter from body.
_OPENING_DELIMITER = "---\n"
_CLOSING_SEQUENCE = "\n---\n\n"


def parse_frontmatter(raw_content: str) -> tuple[dict[str, Any], str]:
    """
    Split raw markdown file content into (frontmatter, body).

    Raises ValidationError if the content is not well-formed: missing
    opening/closing '---' delimiters, or the YAML block does not parse
    to a mapping.
    """
    if not raw_content.startswith(_OPENING_DELIMITER):
        raise ValidationError("content does not start with '---' frontmatter delimiter")

    # Search from the opening delimiter's own trailing newline so an empty
    # frontmatter block ("---\n---\n\n...") is still found correctly.
    search_start = len(_OPENING_DELIMITER) - 1
    closing_index = raw_content.find(_CLOSING_SEQUENCE, search_start)
    if closing_index == -1:
        raise ValidationError("closing '---' frontmatter delimiter not found")

    yaml_block = raw_content[len(_OPENING_DELIMITER):closing_index]
    body = raw_content[closing_index + len(_CLOSING_SEQUENCE):]

    try:
        frontmatter = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        raise ValidationError(f"invalid frontmatter YAML: {exc}") from exc

    if frontmatter is None:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        raise ValidationError("frontmatter must be a YAML mapping")

    return frontmatter, body


def serialize_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    """
    Inverse of parse_frontmatter. Uses the same yaml.dump kwargs as
    app/ingestion/storage.py so files stay consistent across modules.
    """
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    return f"---\n{yaml_content}---\n\n{body}"
