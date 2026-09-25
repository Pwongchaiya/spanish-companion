"""Interface for the flagged-grammar-error Foundation service.

Mirrors api/services/session_lifecycle/i_session_lifecycle_service.py --
typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason: the reference project itself
co-locates the interface file with its implementation in the same folder.
"""

from typing import List, Optional, Protocol

from api.models.foundations.flag import Flag


class IFlagService(Protocol):
    """External-facing contract for Flag's Foundation service."""

    def list_flags(self) -> List[Flag]:
        """The current flag list.

        Raises nothing: FlagBroker.load_flags() returns [] for a missing or
        corrupt file, and "no flags yet" is a normal state, not an error.
        """
        ...

    def get_flag(self, flag_id: str) -> Flag:
        """Look up a single flag by id.

        Raises FlagValidationException (wrapping NotFoundFlagException) if
        no flag with this id exists in the current list.
        Raises FlagDependencyException (wrapping FlagUnavailableError) if
        the underlying FlagBroker call fails.
        Raises FlagServiceException for any other unexpected failure.
        """
        ...

    def save_flags(self, flags: List[Flag]) -> None:
        """Overwrite the stored flag list with the full current list.

        Raises FlagValidationException (wrapping InvalidFlagStatusException)
        if any flag's `status` is not one of FLAG_STATUSES ("open" |
        "mastered" | "skipped") -- checked before the broker is called, so a
        rejected list is never partially written.
        Raises FlagDependencyException (wrapping FlagUnavailableError) if
        the underlying FlagBroker call fails.
        Raises FlagServiceException for any other unexpected failure.
        """
        ...

    def save_session_flags(self, session_id: int, flags: List[Flag]) -> None:
        """Snapshot this session's flags to their own per-session store, in
        addition to (never instead of) save_flags()'s shared-list overwrite.
        Voice Conversation calls this once at teardown so Session Replay
        (roadmap E3) can recover an older session's flags after a later
        session's save_flags() overwrites the shared list.

        Same validation/exception contract as save_flags().
        """
        ...

    def get_session_flags(self, session_id: int) -> Optional[List[Flag]]:
        """This session's own snapshot, or None if none exists -- a session
        recorded before this feature shipped, or one whose teardown snapshot
        write failed. Callers fall back to list_flags() + a time window in
        that case.

        Raises FlagDependencyException (wrapping FlagUnavailableError) if
        the underlying FlagBroker call fails.
        Raises FlagServiceException for any other unexpected failure.
        """
        ...
