"""Leaf exception raised when a persona with that slug already exists.

Fired by the DB's unique constraint (uq_persona_slug) via IntegrityError; same
shape as AlreadyExistsTopicCoveredException. Wrapped into
PersonaDependencyValidationException (not PersonaValidationException) before
leaving the service.
"""

from api.errors import ApiError


class AlreadyExistsPersonaException(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
