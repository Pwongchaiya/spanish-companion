"""Leaf dependency exception raised when a FlagBroker call fails."""

from api.errors import ApiError


class FlagUnavailableError(ApiError):
    """Raised when FlagBroker.load_flags() / save_flags() fails.

    Name and shape mirror `IngestionUnavailableError`
    (rag/models/ingestion/exceptions/ingestion_unavailable_error.py) --
    both name "the broker behind this is down", not a legitimate empty
    result. No `__init__` override: the inherited ApiError(message,
    inner_exception=None) constructor is message-only already, same as
    IngestionUnavailableError.

    Leaf exception -- always caught and wrapped into
    FlagDependencyException before leaving FlagService, mirroring
    IngestionUnavailableError -> IngestionOrchestrationDependencyException.
    """
