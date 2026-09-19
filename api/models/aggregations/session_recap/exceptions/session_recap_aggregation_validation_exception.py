"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class SessionRecapAggregationValidationException(ApiError):
    """Wraps a Progress-orchestration-tier validation exception for
    consumers, without leaking internals.

    What lands here is ProgressOrchestrationValidationException, carried
    through whole rather than unwrapped -- same shape as
    ProgressOrchestrationValidationException itself
    (api/models/orchestrations/progress/exceptions/).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session recap aggregation validation error occurred. Fix the errors and try again.",
            inner_exception=inner_exception,
        )
