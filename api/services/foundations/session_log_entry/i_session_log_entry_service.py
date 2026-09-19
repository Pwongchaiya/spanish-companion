"""Interface for the session-log-entry Foundation service (roadmap C1/C3).

typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason as ITopicCoveredService.

Pure CRUD only -- no duration maths, no streak counting. Both aggregates
are Orchestration-tier logic, built against this interface in
api/services/orchestrations/progress/progress_service.py.

Distinct from `ISessionLogService` (api/services/foundations/session_log/),
which fronts the session `.log` *file* broker -- see
api/models/foundations/session_log_entry/session_log_entry.py for the
naming rationale.
"""

from datetime import datetime
from typing import Protocol

from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry


class ISessionLogEntryService(Protocol):
    """External-facing contract for SessionLogEntry's Foundation service.

    Method names embed the entity name, matching NL.Core.Users' Service
    interface methods (`AddUserProfileAsync`, `ModifyUserProfileAsync`,
    `RetrieveAllUserProfiles` -- IUserProfileService.cs) via the
    ITopicCoveredService precedent -- verbs stay this project's own
    create/list/complete, but the entity name is not dropped.
    """

    def create_session_log_entry(self, started_at: datetime) -> SessionLogEntry:
        """Insert an in-flight row (ended_at NULL, flag_count 0).

        Raises SessionLogEntryValidationException (wrapping
        InvalidSessionLogEntryException) if started_at is not a datetime.
        Raises SessionLogEntryDependencyException (wrapping
        FailedSessionLogEntryStorageException) if the underlying broker
        call fails.
        Raises SessionLogEntryServiceException for any other unexpected
        failure.
        """
        ...

    def list_session_log_entries(self) -> list[SessionLogEntry]:
        """Every session_log row, ordered by started_at ascending.

        Takes no input, so nothing validation-shaped can fail here.
        Raises SessionLogEntryDependencyException (wrapping
        FailedSessionLogEntryStorageException) if the underlying broker
        call fails.
        Raises SessionLogEntryServiceException for any other unexpected
        failure.
        """
        ...

    def complete_session_log_entry(self, entry_id: int, ended_at: datetime, flag_count: int) -> SessionLogEntry:
        """Set ended_at and flag_count on an in-flight row.

        Raises SessionLogEntryValidationException (wrapping
        InvalidSessionLogEntryException) if entry_id is not a positive int,
        ended_at is not a datetime, or flag_count is not a non-negative
        int; or (wrapping NotFoundSessionLogEntryException) if entry_id
        does not exist.
        Raises SessionLogEntryDependencyException (wrapping
        FailedSessionLogEntryStorageException) if the underlying broker
        call fails.
        Raises SessionLogEntryServiceException for any other unexpected
        failure.
        """
        ...
