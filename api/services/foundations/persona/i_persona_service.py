"""Interface for the persona Foundation service.

typing.Protocol, not abc.ABC, per this project's interface waiver (CLAUDE.md).
Pure CRUD only -- find-or-create/memory-update logic belongs to Processing.
Mirrors api/services/foundations/pronunciation_result/i_pronunciation_result_service.py.

Every method raises PersonaValidationException (wrapping
InvalidPersonaException on bad input, or NotFoundPersonaException where noted),
PersonaDependencyException (wrapping FailedPersonaStorageException) if the
broker call fails, and PersonaServiceException for any other unexpected
failure. create_persona/update_persona additionally raise
PersonaDependencyValidationException (wrapping AlreadyExistsPersonaException)
on a duplicate slug.
"""

from typing import Protocol

from api.models.foundations.persona.persona import Persona


class IPersonaService(Protocol):
    """External-facing contract for Persona's Foundation service."""

    def create_persona(self, persona: Persona) -> Persona:
        """Insert a persona (its `id` is ignored)."""
        ...

    def get_persona_by_id(self, persona_id: int) -> Persona:
        """The persona with this id. NotFound if missing."""
        ...

    def get_persona_by_slug(self, slug: str) -> Persona:
        """The persona with this slug. NotFound if missing."""
        ...

    def list_personas(self) -> list[Persona]:
        """Every persona, by id ascending. Empty list if none."""
        ...

    def update_persona(self, persona: Persona) -> Persona:
        """Overwrite the row at `persona.id`. NotFound if missing."""
        ...

    def delete_persona(self, persona_id: int) -> Persona:
        """Delete the row and return it. NotFound if missing."""
        ...
