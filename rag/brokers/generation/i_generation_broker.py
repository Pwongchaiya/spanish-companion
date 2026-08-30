"""GenerationBroker — external-resource boundary for LLM text generation."""

from typing import Protocol

from rag.errors import RagError


class GenerationError(RagError):
    """Client failure or an empty/None response — the only exception this feature has."""


class GenerationBroker(Protocol):
    """External-resource boundary for LLM text generation."""

    def generate(self, prompt: str) -> str:
        """Send prompt to the LLM, return response text.

        Raises:
            GenerationError: on client failure or an empty/None response.
        """
        ...
