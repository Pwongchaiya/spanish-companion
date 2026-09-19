"""Exposure-tier exception wrapping a failed dependency call."""

from api.errors import ApiError


class SessionRecapAggregationDependencyException(ApiError):
    """Wraps ProgressOrchestrationDependencyException -- the one
    dependency-shaped failure this aggregator's two Orchestration
    dependencies can raise by name (Review's list_flags() has no
    Dependency tier of its own; its failures fall to the catch-all below).
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Session recap aggregation dependency error occurred. Contact support.",
            inner_exception=inner_exception,
        )
