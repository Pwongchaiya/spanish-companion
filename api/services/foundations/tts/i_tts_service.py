"""Interface for the text-to-speech Foundation service.

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as IFlagService/ITopicCoveredService.
"""

from typing import Protocol


class ITtsService(Protocol):
    """External-facing contract for Tts's Foundation service."""

    def synthesize_speech(self, text: str) -> bytes:
        """WAV-encoded audio bytes for the given Spanish text.

        Raises TtsValidationException (wrapping InvalidTtsRequestException)
        if text is None/blank or over the length cap.
        Raises TtsDependencyException (wrapping TtsUnavailableError) if the
        underlying TtsBroker call fails.
        Raises TtsServiceException for any other unexpected failure.
        """
        ...
