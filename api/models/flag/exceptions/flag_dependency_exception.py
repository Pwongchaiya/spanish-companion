"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class FlagDependencyException(ApiError):
    """Wraps FlagUnavailableError -- the FlagBroker call this service
    depends on failed.

    Mirrors IngestionOrchestrationDependencyException's shape
    (rag/models/ingestion/exceptions/ingestion_orchestration_dependency_exception.py).
    No DependencyValidation tier for the same reason cited there: this
    service calls FlagBroker directly (Foundation, one broker, per
    CLAUDE.md's Layer-Agent Mapping), so a broker failure is an
    infrastructure outage, never a rejected input.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Flag dependency error occurred. Contact support.", inner_exception)
