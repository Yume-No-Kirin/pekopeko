"""
Fixed domain enum, re-declared for the API layer's own early request-boundary
validation. Deliberately duplicates the same literal each of ingestion/,
extraction/, and review/ already keeps privately (this project's established
"no module imports another module's internals for shared constants"
convention, applied to the orchestration layer's own pre-check).
"""

VALID_DOMAINS = {"PERSONAL", "FICTION", "LEARNING", "RESEARCH", "PUBLISHING"}
