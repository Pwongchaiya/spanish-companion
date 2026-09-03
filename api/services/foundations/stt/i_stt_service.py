"""Interface for the STT Foundation service.

typing.Protocol, not abc.ABC, per this project's broker/service-interface
waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table).
"""

from typing import Protocol

from pipecat.services.azure.stt import AzureSTTService


class ISttService(Protocol):
    """External-facing contract for STT's Foundation service."""

    def create(self) -> AzureSTTService:
        """A configured, ready-to-connect bilingual Azure STT service.

        Pure pass-through to SttBroker. Raises KeyError on missing Azure
        Speech credentials -- the Orchestrator's existing except KeyError
        -> VoiceConversationConfigError mapping already covers this,
        unchanged from before this move.
        """
        ...
