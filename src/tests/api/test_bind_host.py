"""
AC17: the app's run entry point binds to 127.0.0.1 only, never 0.0.0.0 -
inspected directly in src/app/api/app.py, per the ticket's own wording.
"""
from pathlib import Path


def test_run_entry_point_binds_localhost_only():
    app_py = Path("src/app/api/app.py").read_text(encoding="utf-8")
    assert 'host="127.0.0.1"' in app_py or "host='127.0.0.1'" in app_py
    assert "0.0.0.0" not in app_py
