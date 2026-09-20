"""Validation checks for PersonaService.

Same batched Validate(...)/Is* predicate pattern as
PronunciationResultServiceValidations: every failing field is reported in one
InvalidPersonaException. A None persona is a single "persona" error.
"""

from datetime import datetime
from typing import Optional

from api.models.foundations.persona.exceptions import InvalidPersonaException
from api.models.foundations.persona.persona import Persona


class PersonaServiceValidations:
    """Mixin: raises the leaf exception (with every failing field attached)
    when input does not pass checks."""

    def _validate_persona_on_create(self, persona: Optional[Persona]) -> None:
        self._validate_persona_fields(persona)

    def _validate_persona_on_update(self, persona: Optional[Persona]) -> None:
        self._validate_persona_fields(persona, require_id=True)

    def _validate_persona_id(self, persona_id: object) -> None:
        self._validate((self._is_invalid_id(persona_id), "persona_id", "Persona id is required"))

    def _validate_persona_slug(self, slug: object) -> None:
        self._validate((self._is_blank(slug), "slug", "Slug is required"))

    def _validate_persona_fields(self, persona: Optional[Persona], require_id: bool = False) -> None:
        if persona is None:
            exception = InvalidPersonaException()
            exception.upsert_data_list("persona", "Persona is required")
            raise exception

        self._validate(
            (require_id and self._is_invalid_id(persona.id), "id", "Persona id is required"),
            (self._is_blank(persona.slug), "slug", "Slug is required"),
            (self._is_blank(persona.name), "name", "Name is required"),
            (self._is_blank(persona.setting), "setting", "Setting is required"),
            (persona.memory is not None and not isinstance(persona.memory, str), "memory", "Memory must be text"),
            (not isinstance(persona.updated_at, datetime), "updated_at", "Updated at is required"),
        )

    @staticmethod
    def _is_blank(value: object) -> bool:
        return not isinstance(value, str) or not value.strip()

    @staticmethod
    def _is_invalid_id(value: object) -> bool:
        # bool is an int subclass, so True would otherwise pass as 1.
        return isinstance(value, bool) or not isinstance(value, int) or value <= 0

    @staticmethod
    def _validate(*rules: tuple[bool, str, str]) -> None:
        exception = InvalidPersonaException()
        for condition, field, message in rules:
            if condition:
                exception.upsert_data_list(field, message)
        exception.throw_if_contains_errors()
