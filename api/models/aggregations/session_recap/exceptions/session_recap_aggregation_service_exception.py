"""Exposure-tier catch-all exception for SessionRecapAggregationService."""

from api.errors import ApiError


class SessionRecapAggregationServiceException(ApiError):
    """Catch-all wrapper for any exception not otherwise recognised --
    the final safety net so nothing escapes this service unwrapped.

    `inner_exception` here is always a
    FailedSessionRecapAggregationServiceException, and the raw cause is one
    level further in -- mirrors ProgressOrchestrationServiceException.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session recap aggregation service error occurred. Contact support.",
            inner_exception=inner_exception,
        )
