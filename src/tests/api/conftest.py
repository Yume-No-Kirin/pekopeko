"""
Shared fixtures for src/app/api/ route tests: an isolated Flask test client
per test (vault_root/state_dir under tmp_path, no real Ollama/network calls)
and proposal/source file builders matching TASK-001/003's on-disk contract -
built independently, same module-independence convention already established
in src/tests/review/conftest.py. Fake providers and wait_for_terminal_status
live in _helpers.py, not here, since test modules import them directly.
"""
import uuid
from pathlib import Path

import pytest
import yaml

from src.app.api import ApiSettings, create_app

API_KEY = "test-api-key"


@pytest.fixture
def vault_root(tmp_path):
    root = tmp_path / "vault"
    root.mkdir()
    return root


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    d = tmp_path / "task_state"
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(d))
    return d


@pytest.fixture
def app(vault_root, state_dir):
    settings = ApiSettings(vault_root=vault_root, api_key=API_KEY)
    return create_app(settings)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {"X-API-Key": API_KEY}


@pytest.fixture
def source_file(tmp_path):
    path = tmp_path / "source.md"
    path.write_text("# Test Document\n\nThis is a test source.", encoding="utf-8")
    return path


def _write_frontmatter_file(path: Path, frontmatter: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    path.write_text(f"---\n{yaml_content}---\n\n{body}", encoding="utf-8")


@pytest.fixture
def make_source_file(vault_root):
    def _make(domain="PERSONAL", source_id=None, content="# Source\n\nOriginal source text."):
        source_id = source_id or f"src-{uuid.uuid4().hex[:16]}"
        frontmatter = {
            "id": source_id,
            "type": "source",
            "domain": domain,
            "source_format": "markdown",
            "original_filename": "test.md",
            "content_hash": "deadbeef",
            "ingested_at": "2026-08-24T10:00:00",
            "lifecycle_status": "ACTIVE",
        }
        path = vault_root / domain / "sources" / source_id / f"{source_id}.md"
        _write_frontmatter_file(path, frontmatter, content)
        return source_id, path
    return _make


@pytest.fixture
def make_proposal_file(vault_root, make_source_file):
    def _make(
        domain="PERSONAL",
        proposal_id=None,
        status="PROPOSED",
        proposed_item_type="assertion",
        epistemic_status="direct",
        body="Test assertion text.",
        source_id=None,
        extraction_provider="TestProvider",
        valid_from="2026-08-24T10:00:00",
        valid_until=None,
        created_at="2026-08-24T10:00:00",
        internal_domain=None,
        **extra_frontmatter,
    ):
        if source_id is None:
            source_id, _ = make_source_file(domain=domain)

        proposal_id = proposal_id or f"prop-{uuid.uuid4()}"
        frontmatter = {
            "id": proposal_id,
            "type": "proposal",
            "domain": internal_domain if internal_domain is not None else domain,
            "proposal_status": status,
            "proposed_item_type": proposed_item_type,
            "epistemic_status": epistemic_status,
            "created_at": created_at,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "provenance": {
                "source_id": source_id,
                "extraction_provider": extraction_provider,
            },
        }
        frontmatter.update(extra_frontmatter)
        path = vault_root / domain / "proposals" / proposal_id / f"{proposal_id}.md"
        _write_frontmatter_file(path, frontmatter, body)
        return proposal_id, path
    return _make
