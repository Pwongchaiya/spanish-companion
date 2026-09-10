"""Broker for logging.

Wraps stdlib `logging` so Foundation/Orchestration services can log without
importing `logging` (or loguru) directly themselves — the same seam
`NL.Core.Entitlements.Api/Brokers/Loggings/ILoggingBroker.cs` /
`LoggingBroker.cs` plays in the reference project. Extended (H2 audit
finding) from error-only to the four levels actually called across `api/`
once the parallel stdlib-`logging`/loguru call sites were collapsed onto
this one broker — still pinned to what's used, not the full source-of-truth
menu (no `log_critical`, nothing calls it).

No flow control, no exception handling, no business logic — this broker
only wraps the stdlib logger call.
"""

from typing import Protocol


class LoggingBroker(Protocol):
    """External-resource boundary for logging."""

    def log_error(self, exception: Exception) -> None:
        """Log `exception` at ERROR level with its traceback."""
        ...

    def log_warning(self, message: str, *args: object) -> None:
        """Log `message` at WARNING level, with %-style lazy `args`."""
        ...

    def log_info(self, message: str, *args: object) -> None:
        """Log `message` at INFO level, with %-style lazy `args`."""
        ...

    def log_debug(self, message: str, *args: object) -> None:
        """Log `message` at DEBUG level, with %-style lazy `args`."""
        ...
