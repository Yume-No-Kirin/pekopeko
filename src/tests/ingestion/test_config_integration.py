"""
AC8: ingest_source() without an explicit state_dir resolves the task-state
directory from config (<task_state.dir>/ingestion) instead of a hardcoded
literal - verified by pointing PEKOPEKO_TASK_STATE_DIR at a tmp_path
fixture, never touching a real ~/.pekopeko.
"""
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.ingestion import ingest_source
from src.app.ingestion.providers.base import ExtractionResult


def test_default_state_dir_resolved_from_env_config(tmp_path, monkeypatch):
    fake_root = tmp_path / "fake_home_state"
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(fake_root))

    vault_root = tmp_path / "vault"
    source_file = tmp_path / "test.md"
    source_file.write_text("# Test Document\n\nSome content.", encoding="utf-8")

    provider = Mock()
    provider.extract.return_value = ExtractionResult(assertions=[])

    result = ingest_source(
        vault_root=vault_root,
        domain="PERSONAL",
        source_path=source_file,
        provider=provider,
    )

    assert result.status == "completed"
    expected_state_dir = fake_root / "ingestion"
    assert expected_state_dir.exists()
    assert list(expected_state_dir.glob("*.json"))
