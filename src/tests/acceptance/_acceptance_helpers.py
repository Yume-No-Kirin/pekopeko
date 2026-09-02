"""
Deterministic fake LLM providers and an independent frontmatter reader for
src/tests/acceptance/. These stand in only for the provider.extract() call
that ingest_source/extract_source depend on (ADI-008) - never for pipeline,
storage, or review logic itself, which always runs for real. Fixed output,
no randomness, no network: this is what keeps every TC-UC0XX-NN in
specs/tests/test-plan.md reproducible across runs.

Not shared with src/tests/ingestion|extraction|api/_helpers.py, matching
this project's established per-directory test-helper isolation convention.
Named _acceptance_helpers.py rather than _helpers.py deliberately: the repo
already has three same-named _helpers.py modules (config/, extraction/,
api/) which collide under pytest's "rootless" import mode (no __init__.py
anywhere under src/tests/) whenever more than one of their directories is
collected in the same run - confirmed independently of this change (see
specs/tests/test-plan.md's "Known pre-existing issue" note). This file uses
a directory-unique name so it doesn't add a fourth collision, without fixing
the pre-existing ones (out of this task's scope).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yaml  # noqa: E402

from src.app.extraction.providers.base import (  # noqa: E402
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
)
from src.app.extraction.providers.base import ExtractionResult as ExtractionPipelineResult  # noqa: E402
from src.app.ingestion.providers.base import ExtractedAssertion  # noqa: E402
from src.app.ingestion.providers.base import ExtractionResult as IngestionPipelineResult  # noqa: E402


class FixedIngestionProvider:
    """Matches app.ingestion.providers.base.Provider. Always returns the same
    fixed assertion(s) unless overridden by the caller."""

    def __init__(self, assertions=None, model="fixed-test-model", temperature=0.0, exc=None):
        self._assertions = assertions if assertions is not None else [
            ExtractedAssertion(text="Alex is the protagonist of the story.", epistemic_status="direct"),
        ]
        self._model = model
        self._temperature = temperature
        self._exc = exc
        self.calls = []

    def extract(self, text, context):
        self.calls.append((text, context))
        if self._exc is not None:
            raise self._exc
        return IngestionPipelineResult(
            assertions=list(self._assertions), model=self._model, temperature=self._temperature
        )


class FixedExtractionProvider:
    """Matches app.extraction.providers.base.Provider. Always returns the same
    fixed entity/event/relationship unless overridden by the caller."""

    def __init__(self, entities=None, events=None, relationships=None, exc=None):
        self._entities = entities if entities is not None else [
            ExtractedEntity(local_id="e1", entity_type="person", text="Alex",
                             epistemic_status="direct"),
            ExtractedEntity(local_id="e2", entity_type="person", text="Bob",
                             epistemic_status="direct"),
        ]
        self._events = events if events is not None else [
            ExtractedEvent(local_id="ev1", text="Alex arrived in the capital.",
                            epistemic_status="direct",
                            starts_at="2026-01-01T00:00:00", ends_at=None),
        ]
        self._relationships = relationships if relationships is not None else [
            ExtractedRelationship(text="Alex knows Bob.", epistemic_status="inferred",
                                   relationship_type="knows", endpoints=["e1", "e2"]),
        ]
        self._exc = exc
        self.calls = []

    def extract(self, text, context):
        self.calls.append((text, context))
        if self._exc is not None:
            raise self._exc
        return ExtractionPipelineResult(
            entities=list(self._entities), events=list(self._events), relationships=list(self._relationships)
        )


def read_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse a '---\\n<yaml>---\\n\\n<body>' file independently of app code -
    same delimiter contract shared by ingestion/, extraction/, and review/."""
    raw = path.read_text(encoding="utf-8")
    assert raw.startswith("---\n"), "file does not start with frontmatter delimiter"
    closing = raw.find("\n---\n\n", len("---\n") - 1)
    assert closing != -1, "no closing frontmatter delimiter found"
    yaml_block = raw[len("---\n"):closing]
    body = raw[closing + len("\n---\n\n"):]
    return yaml.safe_load(yaml_block), body


def write_proposal_frontmatter_file(path: Path, frontmatter: dict, body: str) -> None:
    """Inverse of read_frontmatter - used only to craft a proposal file by
    hand (e.g. a folder/frontmatter domain mismatch), independently of
    app.review.storage.write_proposal_file_in_place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    path.write_text(f"---\n{yaml_content}---\n\n{body}", encoding="utf-8")
