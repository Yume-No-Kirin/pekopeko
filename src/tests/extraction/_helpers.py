"""
Shared test-only helpers for extraction/ tests.

Not a fixture factory that constructs files matching the on-disk contract
independently (like tests/review/conftest.py) - extraction/ tests only
write through the pipeline/storage under test and read the result back,
so all that's needed is a small independent frontmatter reader.
"""
import sys
from pathlib import Path

# Deterministically add the repo root to sys.path regardless of the cwd
# pytest was invoked from, so `from src.app.extraction import ...` always
# resolves - this repo has no pytest.ini/pyproject.toml pinning rootdir.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def read_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse a '---\\n<yaml>---\\n\\n<body>' file independently of app code."""
    import yaml

    raw = path.read_text(encoding="utf-8")
    assert raw.startswith("---\n"), "file does not start with frontmatter delimiter"
    closing = raw.find("\n---\n\n", len("---\n") - 1)
    assert closing != -1, "no closing frontmatter delimiter found"
    yaml_block = raw[len("---\n"):closing]
    body = raw[closing + len("\n---\n\n"):]
    return yaml.safe_load(yaml_block), body
