"""Broker for Voice Conversation's speech-to-text service construction.

Per the architecture decision record, pipecat's own STT/LLM/TTS service
objects are this feature's Broker layer and are not normally re-wrapped.
STT is the one exception, narrowly: BilingualAzureSTTService overrides a
*private* pipecat method (_connect()) to add continuous language
identification, a fragile pin against pipecat-ai's exact version (see
requirements.txt's ==1.8.1 pin). Isolating that construction behind a
broker keeps the fragile override in one place rather than inline in the
Orchestration service. LLM and TTS have no such override and stay bare
pipecat objects, unwrapped, exactly as before.
"""

from typing import Protocol

from pipecat.services.azure.stt import AzureSTTService


class SttBroker(Protocol):
    """External-resource boundary for STT service construction. Raw
    construction only -- no business logic."""

    def create(self) -> AzureSTTService:
        """A configured, ready-to-connect bilingual Azure STT service.

        Raises KeyError if AZURE_SPEECH_KEY/AZURE_SPEECH_REGION are
        missing from the environment -- Voice Conversation's already-
        resolved 2-exception vocabulary (VoiceConversationConfigError)
        wraps this at the Orchestrator, unchanged from today.
        """
        ...
