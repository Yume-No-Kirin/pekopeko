"""
Concrete implementation of the extraction Provider using Ollama.

This is the only module in extraction/ allowed to reference an HTTP
client/LLM SDK directly (ADI-008, Acceptance Criterion 2) - the `requests`
import is deferred into __init__ so that importing this module (or any
other extraction/ module) never requires `requests` to be installed unless
OllamaProvider is actually instantiated.
"""
import json
from dataclasses import dataclass

from .base import (
    VALID_EPISTEMIC_STATUSES,
    ExtractedEntity,
    ExtractedEvent,
    ExtractedRelationship,
    ExtractionResult,
    Provider,
)


@dataclass
class OllamaProviderConfig:
    """Configuration for Ollama provider."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3"
    timeout: int = 60


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
