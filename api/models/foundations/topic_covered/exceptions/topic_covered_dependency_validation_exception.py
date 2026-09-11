"""Exposure-tier exception wrapping a DB-detected business-rule conflict.

Mirrors NL.Core.Users' UserProfileDependencyValidationException
(UserProfileService.Exceptions.cs:151-162) via the
MistakePatternDependencyValidationException precedent: a dependency-tier
cause (a unique-constraint violation), but surfaced as a
client-correctable error — same message shape as
TopicCoveredValidationException — not a "the system is broken" dependency
failure.
"""

from api.errors import ApiError


class TopicCoveredDependencyValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Topic covered validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
