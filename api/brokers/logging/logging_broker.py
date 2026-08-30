"""StdlibLoggingBroker — stdlib `logging`-backed LoggingBroker."""

import logging


class StdlibLoggingBroker:
    """LoggingBroker backed by `logging.getLogger`.

    Uses a fixed logger name ("spanish_companion") rather than `__name__`
    so every broker/service logs to the same named logger regardless of
    which module constructs it — matching the reference project's single
    named logger rather than per-module fan-out.
    """

    def __init__(self, logger_name: str = "spanish_companion") -> None:
        self._logger = logging.getLogger(logger_name)

    def log_error(self, exception: Exception) -> None:
        self._logger.error(str(exception), exc_info=exception)
