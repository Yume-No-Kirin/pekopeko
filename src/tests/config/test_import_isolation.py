"""
AC9: app/config never imports app.ingestion, app.extraction, or app.review -
verified by static inspection (same pattern as extraction's own
test_import_isolation.py).
"""
from _helpers import REPO_ROOT

CONFIG_DIR = REPO_ROOT / "src" / "app" / "config"

FORBIDDEN_PATTERNS = [
    "import app.ingestion", "from app.ingestion", "from ..ingestion", "from ...ingestion",
    "import app.extraction", "from app.extraction", "from ..extraction", "from ...extraction",
    "import app.review", "from app.review", "from ..review", "from ...review",
]


def test_config_module_does_not_import_other_app_modules():
    for py_file in CONFIG_DIR.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in content, f"{pattern!r} found in {py_file}"
