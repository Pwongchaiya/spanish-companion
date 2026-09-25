"""Broker for on-demand Spanish text-to-speech synthesis.

Unlike STT (api/brokers/stt/), which wraps pipecat's streaming
AzureSTTService for the live voice pipeline, this broker has nothing to do
with Voice Conversation's pipecat pipeline -- it's a single-shot, headless
call for the minimal-pair listening drill (roadmap item B6): given text,
return finished WAV bytes, no streaming, no pipeline, no LLM/TTS bare
pipecat object involved.

typing.Protocol, not ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table) -- interface
co-located with its implementation, same as SttBroker/i_stt_broker.py.
"""

from typing import Protocol


class TtsBroker(Protocol):
    """External-resource boundary for one-shot speech synthesis. Raw
    synthesis only -- no business logic, no input validation."""

    def synthesize(self, text: str, rate: float = 1.0) -> bytes:
        """WAV-encoded audio bytes for the given Spanish text.

        Raises whatever the underlying SDK/transport raises on failure
        (network error, bad credentials, synthesis-cancelled result) --
        TtsService is responsible for catching and wrapping this into
        TtsUnavailableError, mirroring how FlagService wraps FlagBroker
        failures rather than the broker wrapping its own.
        """
        ...
