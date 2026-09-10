"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class PracticeLogDependencyException(ApiError):
    """Wraps PracticeLogUnavailableError -- the broker Practice Log depends
    on failed.

    Mirrors rag.models.orchestrations.ingestion.exceptions.IngestionOrchestrationDependencyException's
    shape ("Ingestion dependency error..." -> "Practice log dependency
    error..."). No DependencyValidation tier -- there is no layer beneath
    this Foundation service other than the broker itself, and a broker
    failure here is an infrastructure outage, never a rejected input.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__("Practice log dependency error occurred. Contact support.", inner_exception)
