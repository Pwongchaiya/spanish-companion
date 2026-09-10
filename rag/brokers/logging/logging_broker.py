"""StdlibLoggingBroker — stdlib `logging`-backed LoggingBroker for rag."""

import logging


class StdlibLoggingBroker:
    """LoggingBroker backed by `logging.getLogger`.

    Byte-for-byte the behavior of api/brokers/logging/logging_broker.py's
    StdlibLoggingBroker — same fixed "spanish_companion" logger name, so
    api- and rag-side services land in one stream — reimplemented rather
    than imported, because rag cannot import api.
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
