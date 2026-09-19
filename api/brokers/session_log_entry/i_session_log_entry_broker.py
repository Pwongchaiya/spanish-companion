"""Broker interface for `session_log` persistence (roadmap C1/C3).

`typing.Protocol`, not `ABC`, per CLAUDE.md's Broker-interfaces waiver
(interfaces co-located with their implementation, matching
`NL.Core.Entitlements`/`NL.Core.Users`). Pure CRUD only -- no duration
maths, no streak counting; both aggregates are Orchestration-tier logic
built against this interface in
api/services/orchestrations/progress/progress_service.py.

Not to be confused with `api/brokers/session_log/`'s `SessionLogBroker`,
which writes session `.log`/transcript *files* and has no table behind it.
See api/models/foundations/session_log_entry/session_log_entry.py for why
this one carries the `Entry` suffix.
"""

from datetime import datetime
from typing import Optional, Protocol

from api.models.foundations.session_log_entry.session_log_entry import SessionLogEntry


class ISessionLogEntryBroker(Protocol):
    """External-resource boundary for `session_log` persistence. Raw
    SQLAlchemy CRUD only -- no business logic, no exception handling.

    Method names embed the entity name (`insert_session_log_entry`, not
    `insert`), matching NL.Core.Users' actual storage broker interface
    verbatim (`InsertUserProfileAsync`, `SelectAllUserProfiles`,
    `UpdateUserProfileAsync` --
    NL.Core.Users.Api/Brokers/Storages/IStorageBroker.UserProfiles.cs:14-17).
    """

    def insert_session_log_entry(self, started_at: datetime) -> SessionLogEntry:
        """Insert a new in-flight row: `started_at` set, `ended_at` NULL,
        `flag_count` 0. Returns it with its assigned id, which the caller
        holds until the session ends."""
        ...

    def select_all_session_log_entries(self) -> list[SessionLogEntry]:
        """Every session_log row, ordered by `started_at` ascending.

        Ordering is the broker's job here, not the caller's: C3's streak is
        defined over sessions *in start order*, and Postgres sorts on an
        indexed column far more cheaply than Python re-sorts the whole
        result set. Mirrors SelectAllUserProfiles()'s "give the caller the
        whole set" shape (IStorageBroker.UserProfiles.cs:15), with the one
        ordering guarantee the callers both need.
        """
        ...

    def update_session_log_entry(
        self, entry_id: int, ended_at: datetime, flag_count: int
    ) -> Optional[SessionLogEntry]:
        """Complete an in-flight row: set `ended_at` and `flag_count`.

        Returns None if entry_id doesn't exist -- Foundation maps that to
        NotFoundSessionLogEntryException, same convention as
        ITopicCoveredBroker.touch_topic_covered()'s None-on-missing-id
        return (topic_covered_broker.py), which itself matches
        NL.Core.Users' SelectUserProfileByIdAsync -> null ->
        NotFoundUserProfileException path (UserProfileService.cs:42-53).
        """
        ...
