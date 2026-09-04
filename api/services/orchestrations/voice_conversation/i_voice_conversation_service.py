"""Interface for the Voice Conversation orchestration service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces the same way Session Lifecycle/Review's are.

Naming follows the Session Lifecycle/Review precedent exactly -- the
Protocol is `VoiceConversationService` (feature name) and the concrete
class stays `ConversationOrchestrator`.

Not consumed by an injected interface anywhere in this codebase today (the
CLI entrypoint constructs ConversationOrchestrator directly) -- added to
match every other Orchestration service's file layout rather than leaving
Voice Conversation as the one cited exception.
"""

from typing import Protocol


class VoiceConversationService(Protocol):
    """External-facing contract for Voice Conversation's orchestration
    service."""

    async def run(self) -> None:
        """Run the live voice conversation pipeline until stopped.

        Raises VoiceConversationConfigError (missing/invalid Azure Speech or
        Gemini credentials) or VoiceConversationPipelineError (audio device
        init failure, pipeline setup timeout).
        """
        ...


__all__ = ["VoiceConversationService"]
