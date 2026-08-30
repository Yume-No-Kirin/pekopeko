"""
YAML frontmatter serialization for the extraction pipeline.

Write-side only: this pipeline never reads a proposal/source file back, so
there is no parse_frontmatter here (unlike app/review/frontmatter.py, which
needs to read proposals for review). Independent of ingestion/ and review/'s
code, per this ticket's independence requirement - only the on-disk contract
(app/ingestion/storage.py's exact format) is shared.
"""
from typing import Any

import yaml


def serialize_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    """
    Render frontmatter + body as "---\\n<yaml>---\\n\\n<body>".

    Uses the same yaml.dump kwargs as app/ingestion/storage.py and
    app/review/frontmatter.py so files stay consistent across modules.
    """
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    return f"---\n{yaml_content}---\n\n{body}"
