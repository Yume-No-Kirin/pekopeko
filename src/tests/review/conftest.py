"""
Fixture builders for Proposal/Source files matching TASK-001's on-disk
contract (app/ingestion/storage.py), built independently of app.ingestion
so review/ tests never import that package.
"""
import uuid
from pathlib import Path

import pytest
import yaml


def _write_frontmatter_file(path: Path, frontmatter: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    path.write_text(f"---\n{yaml_content}---\n\n{body}", encoding="utf-8")


@pytest.fixture
def make_source_file(tmp_path):
    def _make(domain="PERSONAL", source_id=None, content="# Source\n\nOriginal source text.", **overrides):
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
        frontmatter.update(overrides)
        path = tmp_path / domain / "sources" / source_id / f"{source_id}.md"
        _write_frontmatter_file(path, frontmatter, content)
        return source_id, path
    return _make


@pytest.fixture
def make_proposal_file(tmp_path, make_source_file):
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
        path = tmp_path / domain / "proposals" / proposal_id / f"{proposal_id}.md"
        _write_frontmatter_file(path, frontmatter, body)
        return proposal_id, path
    return _make


@pytest.fixture
def make_entity_proposal_file(make_proposal_file):
    def _make(**overrides):
        overrides.setdefault("entity_type", "person")
        return make_proposal_file(proposed_item_type="entity", **overrides)
    return _make


@pytest.fixture
def make_event_proposal_file(make_proposal_file):
    def _make(**overrides):
        overrides.setdefault("starts_at", "2026-01-01T00:00:00")
        overrides.setdefault("ends_at", "2026-01-02T00:00:00")
        return make_proposal_file(proposed_item_type="event", **overrides)
    return _make


@pytest.fixture
def make_relationship_proposal_file(make_proposal_file):
    def _make(**overrides):
        overrides.setdefault("relationship_type", "knows")
        overrides.setdefault("endpoints", ["entity-a", "entity-b"])
        return make_proposal_file(proposed_item_type="relationship", **overrides)
    return _make
