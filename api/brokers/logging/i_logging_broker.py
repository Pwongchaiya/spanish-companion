"""Broker for exception logging.

Wraps stdlib `logging` so Foundation services can log an exception without
importing `logging` directly themselves — the same seam
`NL.Core.Entitlements.Api/Brokers/Loggings/ILoggingBroker.cs` /
`LoggingBroker.cs` plays in the reference project, where every Foundation
service logs a wrapped exception via `ILoggingBroker.LogError(exception)`
before re-raising it. Only `log_error` is defined: nothing in this codebase
calls `LogInformation`/`LogWarning`/`LogCritical` yet, and this project's
convention (see `bot_process.py`'s docstring) is to pin brokers to what's
actually used, not the full source-of-truth menu.

No flow control, no exception handling, no business logic — this broker
only wraps the stdlib logger call.
"""

from typing import Protocol


class LoggingBroker(Protocol):
    """External-resource boundary for exception logging."""

    def log_error(self, exception: Exception) -> None:
        """Log `exception` at ERROR level with its traceback."""
        ...
