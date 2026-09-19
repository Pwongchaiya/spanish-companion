"""Interface for the post-session recap Aggregation service (roadmap C2).

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces the same way every other layer's interface here does.

Naming follows Progress's precedent -- the Protocol is the feature name
(`SessionRecapAggregationService` here, since "SessionRecap" alone would
collide with the plain dataclass in api/models/aggregations/session_recap/),
the concrete class is the same name.
"""

from typing import Optional, Protocol

from api.models.aggregations.session_recap.session_recap import SessionRecap


class SessionRecapAggregationService(Protocol):
    """External-facing contract for the post-session recap Aggregation
    service -- CLAUDE.md's first real trigger for the Aggregation layer
    (an Exposer needing more than one Orchestration service)."""

    def get_latest_recap(self) -> Optional[SessionRecap]:
        """The recap for the most recently completed conversation session,
        or None if no session has ever completed.

        Composes ProgressOrchestrationService.get_latest_completed_session()
        (which session, its boundary timestamps, its flag_count) with
        ReviewOrchestrationService.list_flags() (that session's flag
        categories -- flags.json is fully overwritten at the end of every
        session, so "current flags" and "this session's flags" are the same
        list; see SessionRecap's docstring).

        Raises SessionRecapAggregationValidationException (wrapping
        ProgressOrchestrationValidationException) if a dependency rejects an
        input.
        Raises SessionRecapAggregationDependencyException (wrapping
        ProgressOrchestrationDependencyException) if a dependency's
        underlying storage call fails.
        Raises SessionRecapAggregationServiceException for anything else,
        including either dependency's own catch-all ServiceException.
        """
        ...

    def get_latest_recap_speech(self) -> Optional[bytes]:
        """Spanish WAV narration of get_latest_recap() (roadmap E4), or None
        if no session has ever completed. Review Mode only -- never called
        from the live Conversation path.

        Same exception contract as get_latest_recap(); a TTS failure surfaces
        as SessionRecapAggregationServiceException.
        """
        ...


__all__ = ["SessionRecapAggregationService"]
