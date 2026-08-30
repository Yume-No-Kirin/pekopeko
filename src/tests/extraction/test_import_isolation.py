"""
Static-inspection tests: no pipeline/storage/reader code imports an LLM
SDK/HTTP client directly (AC2), and no git usage anywhere in extraction/ (AC9).
"""
from pathlib import Path

from _helpers import REPO_ROOT

EXTRACTION_DIR = REPO_ROOT / "src" / "app" / "extraction"

SDK_IMPORT_PATTERNS = [
    "import requests", "from requests",
    "import httpx", "from httpx",
    "import openai", "from openai",
    "import anthropic", "from anthropic",
]

# Only the concrete Ollama provider is allowed to reference an HTTP client.
NON_PROVIDER_FILES = [
    EXTRACTION_DIR / "pipeline.py",
    EXTRACTION_DIR / "storage.py",
    EXTRACTION_DIR / "task_state.py",
    EXTRACTION_DIR / "frontmatter.py",
    EXTRACTION_DIR / "errors.py",
    EXTRACTION_DIR / "__init__.py",
    EXTRACTION_DIR / "readers" / "base.py",
    EXTRACTION_DIR / "readers" / "markdown_reader.py",
    EXTRACTION_DIR / "providers" / "base.py",
]


def test_non_provider_modules_do_not_import_llm_sdk():
    for file_path in NON_PROVIDER_FILES:
        assert file_path.exists(), f"expected file not found: {file_path}"
        content = file_path.read_text(encoding="utf-8")
        for pattern in SDK_IMPORT_PATTERNS:
            assert pattern not in content, f"{pattern!r} found in {file_path}"


def test_ollama_provider_only_imports_requests_lazily():
    content = (EXTRACTION_DIR / "providers" / "ollama_provider.py").read_text(encoding="utf-8")
    top_level_lines = [
        line.strip() for line in content.splitlines()
        if not line.startswith((" ", "\t"))
    ]
    assert "import requests" not in top_level_lines
    assert "import requests" in content  # present, but only inside __init__


def test_no_git_usage_in_extraction_module():
    git_patterns = ["import git", "from git", "subprocess", "os.system", ".git/"]
    for py_file in EXTRACTION_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in git_patterns:
            assert pattern not in content, f"git-related usage {pattern!r} found in {py_file}"
