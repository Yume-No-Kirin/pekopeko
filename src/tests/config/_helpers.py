"""
Shared test-only helpers for config/ tests.
"""
import sys
from pathlib import Path

# Deterministically add the repo root to sys.path regardless of the cwd
# pytest was invoked from, so `from src.app.config import ...` always
# resolves - this repo has no pytest.ini/pyproject.toml pinning rootdir.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
