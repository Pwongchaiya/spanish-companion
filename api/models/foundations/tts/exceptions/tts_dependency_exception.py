"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class TtsDependencyException(ApiError):
    """Wraps TtsUnavailableError -- the TtsBroker call this service depends
    on failed.

    Mirrors FlagDependencyException's shape
    (api/models/foundations/flag/exceptions/flag_dependency_exception.py).
    No DependencyValidation tier for the same reason cited there: this
    service calls TtsBroker directly (Foundation, one broker, per
    CLAUDE.md's Layer-Agent Mapping), so a broker failure is an
    infrastructure outage, never a rejected input.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Tts dependency error occurred. Contact support.", inner_exception)
