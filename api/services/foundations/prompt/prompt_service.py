"""Foundation service for Voice Conversation's prompt data.

Single broker dependency -> Foundation layer, not Orchestration, per
CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers. No Validations/Exceptions
mixin split: a pure pass-through has neither to split out (matches
HybridRetrievalService's precedent of skipping a file that would be empty).
"""

from api.brokers.prompt import PromptBroker


class PromptService:
    """Owns access to Voice Conversation's system prompt."""

    def __init__(self, prompt_broker: PromptBroker) -> None:
        self._prompt_broker = prompt_broker

    def get_system_prompt(self) -> str:
        return self._prompt_broker.get_system_prompt()
