"""
AC19: no git usage anywhere in src/app/api/ (project-wide no-git-in-implementation
constraint, ADI-001).
"""
from pathlib import Path


def test_no_git_usage_in_api_package():
    api_dir = Path("src/app/api")
    for py_file in api_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "git" not in content.lower(), f"Unexpected 'git' reference in {py_file}"
