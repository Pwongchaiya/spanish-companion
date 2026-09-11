"""Catch-all exposure-tier exception for unexpected TopicCoveredService failures."""

from api.errors import ApiError


class TopicCoveredServiceException(ApiError):
    """Wraps any exception not covered by the validation/dependency leaves
    -- TopicCoveredService's safety net, mirroring LearnerProfileServiceException.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected topic covered error occurred.",
            inner_exception,
        )
