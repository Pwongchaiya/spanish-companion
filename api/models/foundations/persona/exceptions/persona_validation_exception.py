"""Exposure-tier exception wrapping a validation-tier leaf exception."""

from api.errors import ApiError


class PersonaValidationException(ApiError):
    """Wraps InvalidPersonaException / NotFoundPersonaException for consumers,
    without leaking internals."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Persona validation error occurred. Fix the errors and try again.",
            inner_exception,
        )
