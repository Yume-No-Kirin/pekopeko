"""
AC14: the API process fails immediately at startup - before accepting any
connection - if PEKOPEKO_VAULT_ROOT or PEKOPEKO_API_KEY is unset.
"""
import threading

import pytest

from src.app.api import create_app
from src.app.api.settings import ApiSettings, MissingSettingError, load_settings


def test_missing_vault_root_raises_at_startup(monkeypatch):
    monkeypatch.delenv("PEKOPEKO_VAULT_ROOT", raising=False)
    monkeypatch.setenv("PEKOPEKO_API_KEY", "some-key")

    with pytest.raises(MissingSettingError):
        load_settings()


def test_missing_api_key_raises_at_startup(monkeypatch, tmp_path):
    monkeypatch.setenv("PEKOPEKO_VAULT_ROOT", str(tmp_path))
    monkeypatch.delenv("PEKOPEKO_API_KEY", raising=False)

    with pytest.raises(MissingSettingError):
        load_settings()


def test_both_set_succeeds(monkeypatch, tmp_path):
    monkeypatch.setenv("PEKOPEKO_VAULT_ROOT", str(tmp_path))
    monkeypatch.setenv("PEKOPEKO_API_KEY", "some-key")

    settings = load_settings()
    assert settings.api_key == "some-key"
    assert str(settings.vault_root) == str(tmp_path)


# ADI-013/TASK-001f/TASK-014b: create_app's folder-watcher wiring.

def test_create_app_does_not_start_watcher_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(tmp_path / "state"))
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    settings = ApiSettings(vault_root=vault_root, api_key="test-key")

    threads_before = threading.active_count()
    create_app(settings)

    # folder_watch defaults to disabled - no new thread started.
    assert threading.active_count() == threads_before


def test_create_app_starts_watcher_when_enabled(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("folder_watch:\n  enabled: true\n  poll_interval_seconds: 3600\n", encoding="utf-8")
    monkeypatch.setenv("PEKOPEKO_CONFIG_PATH", str(config_file))
    monkeypatch.setenv("PEKOPEKO_TASK_STATE_DIR", str(tmp_path / "state"))
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    settings = ApiSettings(vault_root=vault_root, api_key="test-key")

    threads_before = threading.active_count()
    create_app(settings)

    assert threading.active_count() > threads_before
