"""
Acceptance criterion 9: no git tooling/libraries used for historization
anywhere in review/.
"""
import re
from pathlib import Path

REVIEW_DIR = Path(__file__).resolve().parents[2] / "app" / "review"

_GIT_PATTERN = re.compile(r"\bgit\b", re.IGNORECASE)


def test_no_git_references_in_review_module():
    py_files = list(REVIEW_DIR.glob("*.py"))
    assert py_files, f"No Python files found under {REVIEW_DIR}"

    for py_file in py_files:
        content = py_file.read_text(encoding="utf-8")
        assert not _GIT_PATTERN.search(content), f"Found 'git' reference in {py_file}"
