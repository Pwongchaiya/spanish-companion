"""Exposure-tier exception wrapping a broker-failure leaf exception."""

from api.errors import ApiError


class PersonaDependencyException(ApiError):
    """Wraps FailedPersonaStorageException for consumers, without leaking
    internals."""

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(
            "Persona data is currently unavailable. Try again shortly.",
            inner_exception,
        )
