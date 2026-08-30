"""Interface for the flagged-grammar-error Foundation service.

Mirrors api/services/session_lifecycle/i_session_lifecycle_service.py --
typing.Protocol, not abc.ABC, per this project's broker-interface waiver
(CLAUDE.md's Phase 2 Layer-Agent Mapping & Waivers table), extended to
service interfaces for the same reason: the reference project itself
co-locates the interface file with its implementation in the same folder.
"""

from typing import List, Protocol

from api.models.flag import Flag


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

        Raises FlagDependencyException (wrapping FlagUnavailableError) if
        the underlying FlagBroker call fails.
        Raises FlagServiceException for any other unexpected failure.
        """
        ...
