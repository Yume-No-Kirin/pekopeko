"""
HTTP/REST API layer for the Knowledge Core (TASK-007, ADI-010): exposes
ingestion/extraction/review/config over Flask. Orchestrates the four
existing packages - does no file I/O of its own beyond list_task_states.
"""
from .app import create_app
from .settings import ApiSettings, MissingSettingError, load_settings

__all__ = [
    'create_app',
    'ApiSettings',
    'MissingSettingError',
    'load_settings',
]
