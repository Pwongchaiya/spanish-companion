"""Catch-all exposure-tier exception for unexpected MistakePatternService failures."""

from api.errors import ApiError


class MistakePatternServiceException(ApiError):
    """Wraps any exception not covered by the validation/dependency leaves
    -- MistakePatternService's safety net, mirroring LearnerProfileServiceException.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected mistake pattern error occurred.",
            inner_exception,
        )
