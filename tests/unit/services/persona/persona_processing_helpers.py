"""Shared helpers for PersonaProcessingService tests. Fixed literal times only."""

from datetime import datetime
from unittest.mock import Mock

from api.models.foundations.persona.exceptions import NotFoundPersonaException, PersonaValidationException
from api.models.foundations.persona.persona import Persona
from api.services.foundations.persona.i_persona_service import IPersonaService
from api.services.processings.persona import PersonaProcessingService

OLD_TIME = datetime(2026, 1, 1, 8, 0, 0)
NOW = datetime(2026, 1, 2, 10, 0, 0)


def make_service() -> tuple[PersonaProcessingService, Mock]:
    foundation = Mock(spec=IPersonaService)
    return PersonaProcessingService(foundation, clock=lambda: NOW), foundation


def make_persona(**overrides) -> Persona:
    base = dict(id=1, slug="marta", name="Marta", setting="A barista.", memory=None, updated_at=OLD_TIME)
    return Persona(**{**base, **overrides})


def not_found() -> PersonaValidationException:
    return PersonaValidationException(inner_exception=NotFoundPersonaException())
