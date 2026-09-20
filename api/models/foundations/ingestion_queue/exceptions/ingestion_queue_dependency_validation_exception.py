"""Exposure-tier exception wrapping a DB-detected business-rule conflict.

A dependency-tier cause (a unique-constraint violation), but surfaced as a
client-correctable error rather than a "the system is broken" failure.
"""

from api.errors import ApiError


class IngestionQueueDependencyValidationException(ApiError):
    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Ingestion queue validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
