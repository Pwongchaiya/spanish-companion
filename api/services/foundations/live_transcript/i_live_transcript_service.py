"""Interface for the live streaming transcript Foundation service.

typing.Protocol, not abc.ABC, per this project's broker/service-interface
waiver (CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table).
"""

from typing import Protocol


class ILiveTranscriptService(Protocol):
    """External-facing contract for the live transcript Foundation
    service, feeding Review Mode / the SSE endpoint."""

    def clear(self) -> None:
        """Truncate the live transcript file at the start of a new
        session -- a prior run's transcript must not bleed into this one.

        Raises LiveTranscriptDependencyException (wrapping
        LiveTranscriptUnavailableError) if the underlying SessionLogBroker
        call fails.
        Raises LiveTranscriptServiceException for any other unexpected failure.
        """
        ...

    def append(self, role: str, text: str) -> None:
        """Append one conversation turn to the live transcript file.

        Raises LiveTranscriptDependencyException (wrapping
        LiveTranscriptUnavailableError) if the underlying SessionLogBroker
        call fails.
        Raises LiveTranscriptServiceException for any other unexpected failure.
        """
        ...

    def read_full_text(self) -> str:
        """Read back the just-ended session's transcript as plain text
        ("[role] text" per line, same shape as
        ConversationOrchestrationService._extract_turns), for the roadmap A6
        CEFR estimate. Returns "" if no transcript was written this session.

        Raises LiveTranscriptDependencyException (wrapping
        LiveTranscriptUnavailableError) if the underlying SessionLogBroker
        call fails.
        Raises LiveTranscriptServiceException for any other unexpected failure.
        """
        ...
