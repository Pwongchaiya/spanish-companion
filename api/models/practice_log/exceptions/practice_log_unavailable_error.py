"""Leaf dependency exception raised when a broker call fails."""

from api.errors import ApiError


class PracticeLogUnavailableError(ApiError):
    """Raised when PracticeLogBroker's underlying file I/O fails.

    Name and shape mirror rag.models.ingestion.exceptions.IngestionUnavailableError
    -- "the infrastructure behind this feature is down", distinct from a
    legitimate empty/zero result. Raised at both broker call sites
    (record_attempt, read_attempts) in _PracticeLogServiceBase.

    Leaf exception -- always caught and wrapped into
    PracticeLogDependencyException before leaving the service, mirroring
    IngestionUnavailableError -> IngestionOrchestrationDependencyException.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
