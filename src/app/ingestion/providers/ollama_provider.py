"""
Concrete implementation of LLM provider using Ollama.
"""
import html
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .base import Provider, ExtractionResult, ExtractedAssertion
from ..storage import scan_existing_assertion_folders, scan_proposed_path_segments

# Every assertion must have a dedicated folder path (Cleo, 2026-09-04, amending
# ADI-012's "degrade to empty" default): if the extraction call's own optional
# "| <path>" suffix (see _build_extraction_prompt) is absent, a second, focused
# call proposes one. FALLBACK_PATH_SEGMENTS is used only if that second call
# still fails to yield a usable path after PATH_PROPOSAL_MAX_ATTEMPTS retries.
PATH_PROPOSAL_MAX_ATTEMPTS = 3
FALLBACK_PATH_SEGMENTS = ["uncategorized"]

# Nomenclature enforcement (ADI-015, amends ADI-014): the model doesn't reliably
# follow prompt-only formatting rules, so every raw path string is run through
# _normalize_path_string regardless of source - a deterministic safety net, not a
# suggestion. Splitting on separators happens BEFORE stopword filtering, so a
# connector word glued in with underscores/hyphens (e.g. "cooperation_vs_pouvoir")
# still gets caught - a \b-based regex substitution on the raw string would not,
# since "_" counts as a word character and blocks the word boundary.
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
            done_reason = result_data.get("done_reason")

            # Parse the extracted assertions from the LLM response
            assertions = self._parse_assertions(extracted_text)

            if not assertions:
                raise ValueError(
                    f"Ollama returned 0 assertions (done_reason={done_reason!r}, "
                    f"model={self.config.model!r}, response_chars={len(extracted_text)})"
                )

            self._ensure_path_segments(assertions, text, context)
            self._resolve_context(assertions, text, context)

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
5. Write each assertion in the same language as the input text. Do not
   translate it into English or any other language.
6. Optionally, propose a short folder path for where this assertion belongs, as a
   ` | <segment1>/<segment2>/...` suffix appended to the line. Omit the suffix entirely
   if you have no proposal. Folder path rules:
   - Each segment is exactly one lowercase French word, no accents, no special
     characters (no "&", no underscores, no hyphens).
   - Never join two ideas into one segment (not "enjeux_thematiques", not
     "conflit_vs_pouvoir") - put each idea in its own segment instead.
   - Order segments from the broadest/general category to the most specific.
   - Bad: `mission/intrigue_academie/conflict Escalation`
     Good: `intrigue/mission/conflit/escalation`

Return only the extracted assertions, one per line, with format:
<epistemic_status>: <assertion_text>
<epistemic_status>: <assertion_text> | <segment1>/<segment2>/...

Example response format (illustrating the format only - match the input
text's language instead of English if it differs):
inferred: The main character was born in a small town.
direct: The author published this book in 2023. | mythologie/japonaise/kitsune
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

            # Split off the optional " | <segment1>/<segment2>/..." path suffix first,
            # so the existing "<epistemic_status>: <assertion_text>" parse below runs
            # unchanged on whatever remains.
            if ' | ' in line:
                line, path_part = line.split(' | ', 1)
                line = line.strip()
            else:
                path_part = None

            proposed_path_segments = []
            if path_part is not None and path_part.strip():
                proposed_path_segments = _normalize_path_string(path_part.strip())

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

                assertions.append(ExtractedAssertion(
                    text=text, epistemic_status=status, proposed_path_segments=proposed_path_segments
                ))
            else:
                # If no status is provided, we should raise an error to maintain quality
                raise ValueError("LLM response must include epistemic status for each assertion in format 'status: text'")

        return assertions

    def _ensure_path_segments(self, assertions: list[ExtractedAssertion], source_text: str, context: dict) -> None:
        """Guarantee every assertion has a non-empty proposed_path_segments, mutating
        in place. The extraction prompt's own optional "| <path>" suffix already fills
        most of these; for any assertion it missed, a dedicated per-assertion call
        proposes one, retried up to PATH_PROPOSAL_MAX_ATTEMPTS times before falling
        back to FALLBACK_PATH_SEGMENTS.

        existing_folders (ADI-015, amends ADI-014) seeds from both the canonical,
        accepted tree and paths already proposed by not-yet-accepted Proposals from
        earlier ingestions, then grows in place as this batch resolves each
        assertion - so assertion #40 of a note can see the path assertion #12 of the
        *same* note just chose, before anything is written to disk."""
        if all(assertion.proposed_path_segments for assertion in assertions):
            return

        existing_folders: list[str] = []
        vault_root = context.get("vault_root")
        domain = context.get("domain")
        if vault_root is not None and domain is not None:
            accepted = scan_existing_assertion_folders(Path(vault_root), domain)
            pending = scan_proposed_path_segments(Path(vault_root), domain)
            existing_folders = sorted(set(accepted) | set(pending))

        for assertion in assertions:
            if not assertion.proposed_path_segments:
                assertion.proposed_path_segments = self._propose_path_with_retry(
                    assertion.text, source_text, existing_folders
                )
            path_str = "/".join(assertion.proposed_path_segments)
            if path_str and path_str not in existing_folders:
                existing_folders.append(path_str)

    def _resolve_context(self, assertions: list[ExtractedAssertion], source_text: str, context: dict) -> None:
        """Populate `context` on every assertion, mutating in place - once per
        `extract()` call, not once per assertion (ADI-016: a novel's code name or
        a life-area doesn't vary between items extracted from the same note).

        Primary signal: the source file's own folder location under _inbox/
        (_derive_source_context). Fallback, only when that yields nothing: a
        single LLM call guessing whether the note belongs to a distinct
        project/universe. Unlike _ensure_path_segments' FALLBACK_PATH_SEGMENTS,
        there is no forced non-null fallback here - context stays None when
        genuinely undetermined (ADI-016)."""
        resolved = self._derive_source_context(context)
        if resolved is None:
            resolved = self._derive_llm_context(source_text)
        for assertion in assertions:
            assertion.context = resolved

    def _derive_source_context(self, context: dict) -> Optional[str]:
        """First subfolder name under <inbox_dirname>/ that `source_path` sits in,
        normalized - or None if there is no such subfolder (file directly in
        inbox/ or inbox/processed/), source_path is outside the inbox tree
        entirely, or any required context key is missing. Never raises
        (INV-019) - a bad/foreign source_path is a safe degrade to None, not a
        failure."""
        source_path = context.get("source_path")
        vault_root = context.get("vault_root")
        domain = context.get("domain")
        inbox_dirname = context.get("inbox_dirname")
        processed_dirname = context.get("processed_dirname")
        if not all([source_path, vault_root, domain, inbox_dirname, processed_dirname]):
            return None
        try:
            inbox_dir = Path(vault_root).resolve() / domain / inbox_dirname
            rel_parts = Path(source_path).resolve().relative_to(inbox_dir).parts
        except (ValueError, OSError):
            return None
        if rel_parts and rel_parts[0] == processed_dirname:
            rel_parts = rel_parts[1:]
        if len(rel_parts) < 2:
            return None
        normalized = _normalize_path_string(rel_parts[0])
        return "-".join(normalized) if normalized else None

    def _derive_llm_context(self, source_text: str) -> Optional[str]:
        """One-shot LLM fallback, retried up to PATH_PROPOSAL_MAX_ATTEMPTS times
        (same attempt count as path proposal, unrelated semantics). Unlike
        _propose_path_with_retry, exhausting retries or an ambiguous/empty
        response resolves to None - never a forced non-empty value."""
        for _ in range(PATH_PROPOSAL_MAX_ATTEMPTS):
            try:
                guess = self._propose_context(source_text)
            except Exception:
                continue
            if guess:
                return guess
            return None
        return None

    def _propose_context(self, source_text: str) -> Optional[str]:
        prompt = self._build_context_prompt(source_text)
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
        if not first_line or first_line.lower() in ("none", "aucun", "aucune", "n/a"):
            return None
        normalized = _normalize_path_string(first_line)
        return "-".join(normalized) if normalized else None

    def _build_context_prompt(self, source_text: str) -> str:
        return f"""You are organizing notes inside a personal knowledge vault.

Note content:
{source_text}

Does this note's content clearly belong to a specific, distinct ongoing
project or fictional universe (e.g. a particular novel, a named long-running
project) rather than general, one-off domain content? If yes, respond with
ONLY a short name for that project/universe (one or two lowercase French
words, no accents, no punctuation). If no, or if you are unsure, respond with
ONLY the word: none

Example responses: "tatouages", "none"
"""

    def _propose_path_with_retry(self, assertion_text: str, source_text: str, existing_folders: list[str]) -> list[str]:
        for _ in range(PATH_PROPOSAL_MAX_ATTEMPTS):
            try:
                segments = self._propose_path(assertion_text, source_text, existing_folders)
                if segments:
                    return segments
            except Exception:
                pass
        return list(FALLBACK_PATH_SEGMENTS)

    def _propose_path(self, assertion_text: str, source_text: str, existing_folders: list[str]) -> list[str]:
        prompt = self._build_path_prompt(assertion_text, source_text, existing_folders)
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

    def _build_path_prompt(self, assertion_text: str, source_text: str, existing_folders: list[str]) -> str:
        folders_block = "\n".join(f"- {folder}" for folder in existing_folders) if existing_folders else "(none yet)"
        return f"""You are organizing extracted knowledge into folders inside a personal knowledge vault.

Full note content (for context):
{source_text}

Existing folder paths already used in this vault (reuse one if it clearly fits;
otherwise propose a new one consistent with this style):
{folders_block}

For the specific assertion below (extracted from the note above), propose a short
folder path (2-4 segments) describing where it thematically belongs. Rules:
- Each segment is exactly one lowercase French word, no accents, no special
  characters (no "&", no underscores, no hyphens), "/" as separator between segments.
- Never join two ideas into one segment (not "enjeux_thematiques", not
  "conflit_vs_pouvoir") - put each idea in its own segment instead.
- Order segments from the broadest/general category to the most specific.
- Bad: `mission/intrigue_academie/conflict Escalation`
  Good: `intrigue/mission/conflit/escalation`

Assertion:
{assertion_text}

Respond with ONLY the folder path, nothing else. Example: mythologie/japonaise/kitsune
"""
