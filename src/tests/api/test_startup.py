"""
AC14: the API process fails immediately at startup - before accepting any
connection - if PEKOPEKO_VAULT_ROOT or PEKOPEKO_API_KEY is unset.
"""
import pytest

from src.app.api.settings import MissingSettingError, load_settings


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
