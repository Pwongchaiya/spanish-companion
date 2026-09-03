"""Interface for the prompt-data Foundation service.

typing.Protocol, not abc.ABC, per this project's broker/service-interface
waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table).
"""

from typing import Protocol


class IPromptService(Protocol):
    """External-facing contract for Prompt's Foundation service."""

    def get_system_prompt(self) -> str:
        """Voice Conversation's system prompt.

        A pure pass-through to PromptBroker -- ponytail: no blank/missing
        check here. The prompt is a repo-committed static asset, not user
        input; a missing file already raises FileNotFoundError (an
        OSError), which the Orchestrator's existing except OSError ->
        VoiceConversationPipelineError mapping already covers, per Voice
        Conversation's already-resolved 2-exception vocabulary (CLAUDE.md).
        Add a blank-content guard only if a real corrupted-deploy incident
        ever makes that a live failure mode.
        """
        ...
