"""Interface for the voice-conversation session lifecycle service.

Mirrors NL.Core.Entitlements.Api/Services/Foundations/Entitlements/
IEntitlementService.cs:12-19 -- typing.Protocol, not abc.ABC, per this
project's existing broker-interface waiver (CLAUDE.md's Phase 2
Layer-Agent Mapping & Waivers table), extended here to service interfaces
for the same reason: the reference project itself co-locates the interface
file with its implementation in the same folder.
"""

from typing import Optional, Protocol

from api.models.foundations.session_lifecycle.session_status import SessionStatus


class SessionLifecycleService(Protocol):
    """External-facing contract for Session Lifecycle's Foundation service."""

    def start(self, scenario_text: Optional[str] = None) -> None:
        """Start the voice-conversation subprocess.

        `scenario_text`, if given, overrides the subprocess's own default
        session-scenario suggestion (LearnerProfile Phase 3).

        Raises SessionValidationException (wrapping AlreadyRunningSessionException)
        if a session is already running.
        """
        ...

    def stop(self) -> None:
        """Stop the running voice-conversation subprocess via the graceful ->
        terminate -> kill escalation.

        Raises SessionValidationException (wrapping NotRunningSessionException)
        if no session is running.
        """
        ...

    def get_status(self) -> SessionStatus:
        """Return the current running/ready/graceful snapshot for the session."""
        ...
