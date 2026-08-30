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
