"""Exposure-tier exception wrapping a DB-detected business-rule conflict.

Mirrors NL.Core.Users' UserProfileDependencyValidationException
(UserProfileService.Exceptions.cs:151-162): a dependency-tier cause
(a unique-constraint violation), but surfaced as a client-correctable
error -- same message shape as MistakePatternValidationException -- not a
"the system is broken" dependency failure.
"""

from api.errors import ApiError


class MistakePatternDependencyValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Mistake pattern validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
