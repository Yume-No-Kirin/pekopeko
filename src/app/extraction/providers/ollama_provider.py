"""
Concrete implementation of the extraction Provider using Ollama.

This is the only module in extraction/ allowed to reference an HTTP
client/LLM SDK directly (ADI-008, Acceptance Criterion 2) - the `requests`
import is deferred into __init__ so that importing this module (or any
other extraction/ module) never requires `requests` to be installed unless
OllamaProvider is actually instantiated.
"""
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .base import (
    VALID_EPISTEMIC_STATUSES,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractionResult,
    Provider,
)
from ..storage import scan_existing_item_folders, scan_proposed_path_segments

# Every entity/event/relationship must have a dedicated folder path (TASK-005a,
# ADI-012 adoption - mirrors ADI-014's mandatory-path guarantee for ingestion's
# OllamaProvider). Resolved once per source note per type (not per item, unlike
# ingestion's per-assertion granularity - V1 scope decision 3): one call per
# non-empty type, up to PATH_PROPOSAL_MAX_ATTEMPTS retries each, falling back to
# FALLBACK_PATH_SEGMENTS if a type's call still fails to yield a usable path.
PATH_PROPOSAL_MAX_ATTEMPTS = 3
FALLBACK_PATH_SEGMENTS = ["uncategorized"]

# Nomenclature enforcement (ADI-015 posture, independently reimplemented here -
# no import from ingestion/, per this ticket's module-independence requirement).
# Splitting on separators happens BEFORE stopword filtering, so a connector word
# glued in with underscores/hyphens (e.g. "cooperation_vs_pouvoir") still gets
# caught - a \b-based regex substitution on the raw string would not, since "_"
# counts as a word character and blocks the word boundary.
_PATH_STOPWORDS = {"vs", "et", "and", "de", "du", "des", "la", "le", "les", "l"}
_LIGATURE_TRANSLATION = str.maketrans({"œ": "oe", "Œ": "oe", "æ": "ae", "Æ": "ae"})


def _normalize_path_string(raw: str) -> list[str]:
    """Turn a raw, possibly messy model-proposed path string into clean, single-word,
    unaccented, lowercase segments - a deterministic safety net independent of the
    model actually following the nomenclature rules in the prompt."""
    unescaped = html.unescape(raw)
    segments: list[str] = []
    for part in unescaped.split('/'):
        part = part.replace('&', ' ')
        for token in re.split(r'[\s_\-]+', part):
            token = token.translate(_LIGATURE_TRANSLATION)
            token = unicodedata.normalize('NFKD', token).encode('ascii', 'ignore').decode('ascii')
            token = re.sub(r'[^a-z0-9]', '', token.lower())
            if token and token not in _PATH_STOPWORDS:
                segments.append(token)
    return segments


@dataclass
class OllamaProviderConfig:
    """Configuration for Ollama provider."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout: int = 60
    temperature: float = 0.7


class OllamaProvider(Provider):
    """Concrete implementation of Provider using Ollama API."""

    def __init__(self, config: OllamaProviderConfig = None):
        self.config = config or OllamaProviderConfig()
        # Import requests only when needed to avoid dependency issues
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("OllamaProvider requires 'requests' library. Please install with: pip install requests")

    def extract(self, text: str, context: dict) -> ExtractionResult:
        """
        Extract entities, events, and relationships from text using Ollama.

        Args:
            text: The source text to analyze
            context: Additional context for extraction

        Returns:
            ExtractionResult containing the extracted entities/events/relationships

        Raises:
            Exception: If the extraction fails
        """
        try:
            prompt = self._build_extraction_prompt(text, context)

            response = self.requests.post(
                f"{self.config.base_url}/api/generate",
                json={
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.config.timeout
            )

            response.raise_for_status()

            result_data = response.json()
            extracted_text = result_data.get("response", "")
            done_reason = result_data.get("done_reason")

            if not extracted_text.strip():
                raise ValueError(
                    f"Ollama returned 0 entities/events/relationships (done_reason={done_reason!r}, "
                    f"model={self.config.model!r}, response_chars={len(extracted_text)})"
                )

            result = self._parse_extraction_result(extracted_text)
            if not (result.entities or result.events or result.relationships):
                raise ValueError(
                    f"Ollama returned 0 entities/events/relationships (done_reason={done_reason!r}, "
                    f"model={self.config.model!r}, response_chars={len(extracted_text)})"
                )
            self._ensure_path_segments(result, text, context)
            return result

        except Exception as e:
            raise Exception(f"Failed to extract entities/events/relationships using Ollama: {str(e)}")

    def _build_extraction_prompt(self, text: str, context: dict) -> str:
        """Build the prompt for extraction."""
        prompt = f"""
You are an expert knowledge extraction agent. Extract entities, events, and
relationships from the following text.

Input text:
{text}

Instructions:
1. Entities are distinct, identifiable objects or concepts (people, places,
   organizations, objects, or other discrete items).
2. Events are occurrences or actions situated in a specific time frame.
3. Relationships describe connections between two or more entities/events.
4. Assign every entity and event a short local_id unique within this
   response (e.g. "e1", "e2", "ev1") so relationships can reference them.
5. For every entity/event/relationship, determine the epistemic status:
   - "direct" if explicitly stated in the source
   - "inferred" if logically derived from the text
   - "uncertain" if there is ambiguity or incomplete information
   - "contested" if the statement is disputed or debatable
6. A relationship's endpoints list must reference the local_id of the
   entities/events it connects, and must contain at least 2 identifiers.
7. Write every "text" field in the same language as the input text. Do not
   translate it into English or any other language. (entity_type and
   relationship_type stay in English, as taxonomy labels.)

Return ONLY a single JSON object, no other text, in exactly this shape:
{{
  "entities": [
    {{"local_id": "e1", "entity_type": "person", "text": "...", "epistemic_status": "direct"}}
  ],
  "events": [
    {{"local_id": "ev1", "text": "...", "epistemic_status": "inferred", "starts_at": null, "ends_at": null}}
  ],
  "relationships": [
    {{"text": "...", "epistemic_status": "direct", "relationship_type": "...", "endpoints": ["e1", "ev1"]}}
  ]
}}

Omit any of the three lists (or leave it empty) if nothing of that kind is
present in the text. Now extract from the input text:
"""
        return prompt

    def _parse_extraction_result(self, extracted_text: str) -> ExtractionResult:
        """Parse the JSON extraction result from the LLM response."""
        json_start = extracted_text.find("{")
        json_end = extracted_text.rfind("}")
        if json_start == -1 or json_end == -1 or json_end < json_start:
            raise ValueError("LLM response did not contain a JSON object")

        try:
            data = json.loads(extracted_text[json_start:json_end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response was not valid JSON: {e}")

        entities = [
            self._parse_entity(item) for item in data.get("entities", [])
        ]
        events = [
            self._parse_event(item) for item in data.get("events", [])
        ]
        relationships = [
            self._parse_relationship(item) for item in data.get("relationships", [])
        ]

        return ExtractionResult(entities=entities, events=events, relationships=relationships)

    def _validate_epistemic_status(self, status: str) -> str:
        if status not in VALID_EPISTEMIC_STATUSES:
            raise ValueError(
                f"Invalid epistemic_status '{status}' in LLM response. "
                f"Must be one of {sorted(VALID_EPISTEMIC_STATUSES)}"
            )
        return status

    def _parse_entity(self, item: dict) -> ExtractedEntity:
        return ExtractedEntity(
            local_id=item["local_id"],
            entity_type=item["entity_type"],
            text=item["text"],
            epistemic_status=self._validate_epistemic_status(item["epistemic_status"]),
        )

    def _parse_event(self, item: dict) -> ExtractedEvent:
        return ExtractedEvent(
            local_id=item["local_id"],
            text=item["text"],
            epistemic_status=self._validate_epistemic_status(item["epistemic_status"]),
            starts_at=item.get("starts_at"),
            ends_at=item.get("ends_at"),
        )

    def _parse_relationship(self, item: dict) -> ExtractedRelationship:
        return ExtractedRelationship(
            text=item["text"],
            epistemic_status=self._validate_epistemic_status(item["epistemic_status"]),
            relationship_type=item["relationship_type"],
            endpoints=list(item["endpoints"]),
        )

    def _ensure_path_segments(self, result: ExtractionResult, source_text: str, context: dict) -> None:
        """Guarantee every entity/event/relationship has a non-empty
        proposed_path_segments, mutating in place. Resolved once per type per call
        (not once per item, unlike ingestion's per-assertion granularity) - at most
        three extra Ollama calls regardless of how many items were extracted, and a
        type with zero items triggers no call at all.

        existing_folders (per type, never shared across types - the entity tree and
        the event tree are different taxonomies) seeds from both the canonical,
        accepted tree and paths already proposed by not-yet-accepted Proposals of the
        same type. Unlike ingestion's in-batch accumulation between assertions, there
        is no analogous accumulation here: each type resolves exactly once per call.
        """
        vault_root = context.get("vault_root")
        domain = context.get("domain")
        for item_type, items in (
            ("entity", result.entities),
            ("event", result.events),
            ("relationship", result.relationships),
        ):
            if not items:
                continue

            existing_folders: list[str] = []
            if vault_root is not None and domain is not None:
                accepted = scan_existing_item_folders(Path(vault_root), domain, item_type)
                pending = scan_proposed_path_segments(Path(vault_root), domain, item_type)
                existing_folders = sorted(set(accepted) | set(pending))

            segments = self._propose_path_with_retry(item_type, items, source_text, existing_folders)
            for item in items:
                item.proposed_path_segments = list(segments)

    def _propose_path_with_retry(
        self, item_type: str, items: list, source_text: str, existing_folders: list[str]
    ) -> list[str]:
        for _ in range(PATH_PROPOSAL_MAX_ATTEMPTS):
            try:
                segments = self._propose_path(item_type, items, source_text, existing_folders)
                if segments:
                    return segments
            except Exception:
                pass
        return list(FALLBACK_PATH_SEGMENTS)

    def _propose_path(
        self, item_type: str, items: list, source_text: str, existing_folders: list[str]
    ) -> list[str]:
        prompt = self._build_path_prompt(item_type, items, source_text, existing_folders)
        response = self.requests.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": self.config.temperature}
            },
            timeout=self.config.timeout
        )
        response.raise_for_status()
        raw = response.json().get("response", "").strip()
        first_line = raw.splitlines()[0].strip() if raw else ""
        return _normalize_path_string(first_line)

    def _build_path_prompt(
        self, item_type: str, items: list, source_text: str, existing_folders: list[str]
    ) -> str:
        type_labels = {"entity": "entities", "event": "events", "relationship": "relationships"}
        type_label = type_labels[item_type]
        folders_block = "\n".join(f"- {folder}" for folder in existing_folders) if existing_folders else "(none yet)"
        items_block = "\n".join(f"- {item.text}" for item in items)
        return f"""You are organizing extracted knowledge into folders inside a personal knowledge vault.

Full note content (for context):
{source_text}

Existing folder paths already used in this vault (reuse one if it clearly fits;
otherwise propose a new one consistent with this style):
{folders_block}

The following {type_label} were all extracted from the note above. Propose ONE short
folder path (2-4 segments) that fits all of them together thematically. Rules:
- Each segment is exactly one lowercase French word, no accents, no special
  characters (no "&", no underscores, no hyphens), "/" as separator between segments.
- Never join two ideas into one segment (not "enjeux_thematiques", not
  "conflit_vs_pouvoir") - put each idea in its own segment instead.
- Order segments from the broadest/general category to the most specific.
- Bad: `mission/intrigue_academie/conflict Escalation`
  Good: `intrigue/mission/conflit/escalation`

{type_label.capitalize()}:
{items_block}

Respond with ONLY the folder path, nothing else. Example: mythologie/japonaise/kitsune
"""
