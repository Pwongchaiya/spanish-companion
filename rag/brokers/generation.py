"""Broker for the Gemini generation client.

Phase 1 (review/review.py) constructed a fresh genai.Client() inside
explain_flag() on every call. This broker is the single source of truth:
one client instance, constructed once in __init__ and reused for every
generate() call.

No DB, no SQLAlchemy — the Gemini API is the only external resource here.
"""

import os
from typing import Optional, Protocol

import google.genai as genai

# Matches voice/bot.py's and review/review.py's existing default exactly —
# Gemini Flash-Lite, per CLAUDE.md tech stack.
_DEFAULT_MODEL_NAME = "gemini-flash-lite-latest"


class GenerationError(Exception):
    """Client failure or an empty/None response — the only exception this feature has."""


class GenerationBroker(Protocol):
    """External-resource boundary for LLM text generation."""

    def generate(self, prompt: str) -> str:
        """Send prompt to the LLM, return response text.

        Raises:
            GenerationError: on client failure or an empty/None response.
        """
        ...


class GeminiGenerationBroker:
    """GenerationBroker backed by google-genai's Gemini client.

    `api_key`/`model_name` default to GEMINI_API_KEY/GEMINI_MODEL (env),
    then the project's pinned Flash-Lite default — same defaulting shape as
    api/brokers/bot_process.py's `command`/`cwd`.

    # ponytail: broker-skill's "no try/except in a broker" default is
    # deliberately not followed here — the empty/None-response guard and
    # client-failure wrap into GenerationError are the explicit, only
    # exception this feature has (per CLAUDE.md's Foundation waiver for
    # Generation), and this is an external-dependency failure mode with
    # nowhere else to live given this project's 3-layer Broker/Service/
    # Controller architecture. A later GenerationService catches
    # GenerationError and substitutes a fallback string.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        resolved_api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self._model_name = model_name if model_name is not None else os.getenv("GEMINI_MODEL", _DEFAULT_MODEL_NAME)
        self._client = genai.Client(api_key=resolved_api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(model=self._model_name, contents=prompt)
        except Exception as e:
            raise GenerationError(f"Gemini client call failed: {e}") from e

        # response.text can be None (e.g. safety-blocked/empty candidate)
        # even without raising — same behavior review/review.py guarded
        # against, now enforced as the broker's contract instead of left
        # to each caller.
        text = getattr(response, "text", None)
        if not text:
            raise GenerationError("Gemini returned an empty or None response")
        return text
