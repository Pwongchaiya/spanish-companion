"""Leaf validation exception raised when a persona row doesn't exist.

Raised by the service when the broker returns None for a lookup by id/slug,
or for update/delete of a missing id. list_personas() returns an empty list
instead -- "no rows" isn't a not-found condition.
"""

from api.errors import ApiError


class NotFoundPersonaException(ApiError):
    """Leaf exception -- always caught and wrapped into
    PersonaValidationException before leaving PersonaService."""

    def __init__(self) -> None:
        super().__init__("No persona row exists for that lookup")
