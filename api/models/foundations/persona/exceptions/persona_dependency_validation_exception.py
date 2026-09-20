"""Exposure-tier exception wrapping a DB-detected business-rule conflict
(duplicate slug). Same shape as TopicCoveredDependencyValidationException:
a dependency-tier cause surfaced as a client-correctable error."""

from api.errors import ApiError


class PersonaDependencyValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Persona validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
