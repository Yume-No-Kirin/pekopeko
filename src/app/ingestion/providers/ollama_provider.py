"""
Concrete implementation of LLM provider using Ollama.
"""
import json
import os
from typing import Dict, Any
from dataclasses import dataclass
from .base import Provider, ExtractionResult, ExtractedAssertion


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
        Extract assertions from text using Ollama.

        Args:
            text: The source text to analyze
            context: Additional context for extraction

        Returns:
            ExtractionResult containing the extracted assertions

        Raises:
            Exception: If the extraction fails
        """
        try:
            # Prepare the prompt for the LLM
            prompt = self._build_extraction_prompt(text, context)

            # Make request to Ollama API
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

            # Parse the response
            result_data = response.json()
            extracted_text = result_data.get("response", "")

            # Parse the extracted assertions from the LLM response
            assertions = self._parse_assertions(extracted_text)

            return ExtractionResult(
                assertions=assertions,
                model=self.config.model,
                temperature=self.config.temperature
            )

        except Exception as e:
            raise Exception(f"Failed to extract assertions using Ollama: {str(e)}")

    def _build_extraction_prompt(self, text: str, context: dict) -> str:
        """Build the prompt for extraction."""
        prompt = f"""
You are an expert knowledge extraction agent. Extract atomic assertions from the following text.
Each assertion should be a self-contained statement that can be stored as a knowledge item.

Input text:
{text}

Instructions:
1. Extract only atomic, factual assertions (not opinions or interpretations)
2. Each assertion must be in a clear, declarative sentence
3. If multiple facts are present, extract them separately
4. For each assertion, determine the epistemic status:
   - "direct" if the fact is explicitly stated in the source
   - "inferred" if it's logically derived from the text
   - "uncertain" if there's ambiguity or incomplete information
   - "contested" if the statement is disputed or debatable

Return only the extracted assertions, one per line, with format:
<epistemic_status>: <assertion_text>

Example response format:
inferred: The main character was born in a small town.
direct: The author published this book in 2023.
uncertain: The exact date of the event is unknown.
contested: The theory is widely debated among experts.

Now extract from the input text:
"""
        return prompt

    def _parse_assertions(self, extracted_text: str) -> list[ExtractedAssertion]:
        """Parse assertions from LLM response."""
        assertions = []
        for line in extracted_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue

            # Parse the format "<epistemic_status>: <assertion_text>"
            if ': ' in line:
                status, text = line.split(': ', 1)
                status = status.strip()
                text = text.strip()

                # Validate epistemic status
                valid_statuses = ["direct", "inferred", "uncertain", "contested"]
                if status not in valid_statuses:
                    # Raise an error instead of defaulting - this ensures quality control
                    raise ValueError(f"Invalid epistemic_status '{status}' in LLM response. Must be one of {valid_statuses}")

                assertions.append(ExtractedAssertion(text=text, epistemic_status=status))
            else:
                # If no status is provided, we should raise an error to maintain quality
                raise ValueError("LLM response must include epistemic status for each assertion in format 'status: text'")

        return assertions