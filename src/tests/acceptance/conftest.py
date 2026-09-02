"""
Shared fixtures for src/tests/acceptance/: tmp_path-rooted vault/state dirs
for direct pipeline calls (ingest_source, extract_source, review.*), no
Flask, no network. See specs/tests/test-plan.md's "Test layers" section.
"""
import pytest


@pytest.fixture
def vault_root(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def state_dir(tmp_path):
    return tmp_path / "task_state"


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "novel.md"
    path.write_text(
        "# Chapter One\n\nAlex traveled to the capital city in early spring. "
        "Bob was waiting at the gate.",
        encoding="utf-8",
    )
    return path
