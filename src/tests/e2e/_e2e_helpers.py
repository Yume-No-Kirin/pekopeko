"""
Real-HTTP polling helper for src/tests/e2e/. Named _e2e_helpers.py rather
than _helpers.py deliberately, to avoid adding a fifth collision to the
pre-existing _helpers.py name clash under pytest's rootless import mode
(config/, extraction/, api/, and src/tests/acceptance/'s own
_acceptance_helpers.py already share/avoid this - see
specs/tests/test-plan.md's "Known pre-existing issue" note).
"""
import time

import requests

TERMINAL_STATUSES = {"completed", "failed", "skipped_duplicate"}


def poll_task_until_terminal(base_url, headers, domain, kind, task_id, timeout=180.0, interval=0.5):
    """kind: 'ingestions' or 'extractions'. Polls the real GET endpoint until
    status leaves pending/running, per ADI-010's fire-and-poll contract.
    A real Ollama call is in flight server-side, so the default timeout is
    generous."""
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        resp = requests.get(f"{base_url}/domains/{domain}/{kind}/{task_id}", headers=headers, timeout=10)
        assert resp.status_code == 200, resp.text
        last = resp.json()
        if last["status"] in TERMINAL_STATUSES:
            return last
        time.sleep(interval)
    raise TimeoutError(f"Task {task_id} did not reach a terminal status within {timeout}s (last: {last})")
