"""
API process startup settings (ADI-010 SS4/SS5): vault_root and the shared
API key, read once from the environment when the process starts. Both are
required - the process must fail immediately, before accepting any
connection, if either is unset.

vault_root deliberately stays local to this package - it is never added to
src/app/config's PekopekoConfig schema (TASK-004's own deliberate omission).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class MissingSettingError(Exception):
    """Raised when a required PEKOPEKO_* startup environment variable is unset."""


@dataclass(frozen=True)
class ApiSettings:
    vault_root: Path
    api_key: str


def load_settings() -> ApiSettings:
    # Same bounded, .env-loadable PEKOPEKO_* key convention TASK-004 already
    # established (python-dotenv, already a pinned dependency). A missing
    # .env is not an error - a real process env var always takes priority
    # (override=False).
    load_dotenv(override=False)

    vault_root = os.environ.get("PEKOPEKO_VAULT_ROOT")
    if not vault_root:
        raise MissingSettingError("PEKOPEKO_VAULT_ROOT environment variable is required and unset")

    api_key = os.environ.get("PEKOPEKO_API_KEY")
    if not api_key:
        raise MissingSettingError("PEKOPEKO_API_KEY environment variable is required and unset")

    return ApiSettings(vault_root=Path(vault_root).expanduser(), api_key=api_key)
