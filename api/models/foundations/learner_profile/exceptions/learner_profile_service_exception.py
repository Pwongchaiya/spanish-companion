"""Catch-all exposure-tier exception for unexpected LearnerProfileService failures."""

from api.errors import ApiError


class LearnerProfileServiceException(ApiError):
    """Wraps any exception not covered by the validation/dependency leaves
    -- LearnerProfileService's safety net, mirroring FlagServiceException /
    SessionServiceException.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected learner profile error occurred.",
            inner_exception,
        )
