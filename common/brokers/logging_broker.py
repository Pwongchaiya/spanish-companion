"""StdlibLoggingBroker — stdlib `logging`-backed LoggingBroker.

Shared by api/brokers/logging and rag/brokers/logging: same concrete
implementation, same fixed "spanish_companion" logger name so api- and
rag-side services land in one stream. Each package's own `LoggingBroker`
Protocol stays local (api -> rag is the only allowed dependency direction;
this common module depends on neither).
"""

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

    def log_warning(self, message: str, *args: object) -> None:
        self._logger.warning(message, *args)

    def log_info(self, message: str, *args: object) -> None:
        self._logger.info(message, *args)

    def log_debug(self, message: str, *args: object) -> None:
        self._logger.debug(message, *args)


if __name__ == "__main__":
    # ponytail: smallest possible check — %-style args must not raise, and
    # each level must forward to the right stdlib method.
    broker = StdlibLoggingBroker("selftest")
    broker.log_error(ValueError("boom"))
    broker.log_warning("warn %s", "x")
    broker.log_info("info %s", "x")
    broker.log_debug("debug %s", "x")
    print("ok")
