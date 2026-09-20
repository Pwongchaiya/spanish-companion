"""Catch-all exposure-tier exception for unexpected PersonaService failures."""

from api.errors import ApiError


class PersonaServiceException(ApiError):
    """Wraps any exception not covered by the validation/dependency leaves."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "An unexpected persona error occurred.",
            inner_exception,
        )
