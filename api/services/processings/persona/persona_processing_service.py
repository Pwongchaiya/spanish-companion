"""Processing service for the persona entity.

Higher-order logic on top of the single Foundation dependency (IPersonaService):
find-or-create from static definitions, prompt-brief composition, memory
update. Same shape as MistakePatternProcessingService: no logging broker, no
exception re-wrapping -- Foundation exceptions propagate unchanged; input
validation raises the leaf InvalidPersonaException directly.
"""

from dataclasses import replace
from datetime import datetime
from typing import Callable

from api.data.personas import PERSONAS
from api.models.foundations.persona.exceptions import InvalidPersonaException, PersonaValidationException
from api.models.foundations.persona.exceptions import NotFoundPersonaException
from api.models.foundations.persona.persona import Persona
from api.services.foundations.persona.i_persona_service import IPersonaService


class PersonaProcessingService:
    def __init__(self, persona_service: IPersonaService, clock: Callable[[], datetime] = datetime.now) -> None:
        self._persona_service = persona_service
        self._clock = clock

    def ensure_persona(self, slug: str) -> Persona:
        definition = PERSONAS.get(slug)
        if definition is None:
            exception = InvalidPersonaException()
            exception.upsert_data_list("slug", "Slug is not a known persona")
            exception.throw_if_contains_errors()
        try:
            return self._persona_service.get_persona_by_slug(slug)
        except PersonaValidationException as e:
            if not isinstance(e.inner_exception, NotFoundPersonaException):
                raise
        return self._persona_service.create_persona(
            Persona(
                id=None,
                slug=definition.slug,
                name=definition.name,
                setting=definition.setting,
                memory=None,
                updated_at=self._clock(),
            )
        )

    def get_persona_brief(self, slug: str) -> str:
        persona = self.ensure_persona(slug)
        brief = f"{persona.name}\n{persona.setting}"
        if persona.memory and persona.memory.strip():
            brief += f"\n\nWhat you remember from past chats:\n{persona.memory}"
        return brief

    def update_memory(self, slug: str, memory: str) -> Persona:
        cleaned = memory.strip() if isinstance(memory, str) else ""
        if not cleaned:
            exception = InvalidPersonaException()
            exception.upsert_data_list("memory", "Memory is required")
            exception.throw_if_contains_errors()
        persona = self.ensure_persona(slug)
        return self._persona_service.update_persona(replace(persona, memory=cleaned, updated_at=self._clock()))
