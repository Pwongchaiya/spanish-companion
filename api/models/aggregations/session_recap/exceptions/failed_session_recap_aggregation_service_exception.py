"""Inner-tier exception for a genuinely unexpected failure."""

from api.errors import ApiError


class FailedSessionRecapAggregationServiceException(ApiError):
    """Wraps a raw, unrecognised Exception before it is handed to
    _create_and_log_service_exception. Mirrors
    FailedProgressOrchestrationServiceException.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Failed session recap aggregation service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
