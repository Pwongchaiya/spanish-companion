"""Broker for Voice Conversation's system-prompt data file.

Closes Tri-Nature gap #2 for this feature (SYSTEM_PROMPT was a Python
string literal -- Skills belong in Data, not code), mirroring the same
extraction already done for Generation's prompt templates
(rag/data/prompts/, rag/services/foundations/generation/).
"""

from typing import Protocol


class PromptBroker(Protocol):
    """External-resource boundary for prompt data files. Raw file I/O
    only -- no validation, no business logic."""

    def get_system_prompt(self) -> str:
        """The full text of Voice Conversation's system prompt, read
        as-is from its data file."""
        ...
