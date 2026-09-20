"""Foundation service for the persona entity.

Wraps IPersonaBroker (api/brokers/persona/) with input validation only --
pure CRUD, no upsert. Single broker dependency -> Foundation layer. Split into
logic + Validations/Exceptions mixins, the concrete class declared here,
mirroring api/services/foundations/pronunciation_result/pronunciation_result_service.py.
The None-check on broker returns is a business check on a normal return value,
same as TopicCoveredService.touch_topic_covered.
"""

from api.brokers.logging import LoggingBroker
from api.brokers.persona.i_persona_broker import IPersonaBroker
from api.models.foundations.persona.exceptions import NotFoundPersonaException
from api.models.foundations.persona.persona import Persona
from api.services.foundations.persona.i_persona_service import IPersonaService
from api.services.foundations.persona.persona_service_exceptions import PersonaServiceExceptions
from api.services.foundations.persona.persona_service_validations import PersonaServiceValidations


class PersonaService(
    PersonaServiceExceptions,
    PersonaServiceValidations,
    IPersonaService,
):
    """Owns Persona CRUD."""

    def __init__(
        self,
        persona_broker: IPersonaBroker,
        *,
        logging_broker: LoggingBroker,
    ) -> None:
        self._persona_broker = persona_broker
        self._logging_broker = logging_broker

    def create_persona(self, persona: Persona) -> Persona:
        def action() -> Persona:
            self._validate_persona_on_create(persona)
            return self._persona_broker.insert_persona(persona)

        return self._try_catch(action)

    def get_persona_by_id(self, persona_id: int) -> Persona:
        def action() -> Persona:
            self._validate_persona_id(persona_id)
            maybe_persona = self._persona_broker.select_persona_by_id(persona_id)
            if maybe_persona is None:
                raise NotFoundPersonaException()
            return maybe_persona

        return self._try_catch(action)

    def get_persona_by_slug(self, slug: str) -> Persona:
        def action() -> Persona:
            self._validate_persona_slug(slug)
            maybe_persona = self._persona_broker.select_persona_by_slug(slug)
            if maybe_persona is None:
                raise NotFoundPersonaException()
            return maybe_persona

        return self._try_catch(action)

    def list_personas(self) -> list[Persona]:
        def action() -> list[Persona]:
            return self._persona_broker.select_all_personas()

        return self._try_catch(action)

    def update_persona(self, persona: Persona) -> Persona:
        def action() -> Persona:
            self._validate_persona_on_update(persona)
            maybe_persona = self._persona_broker.update_persona(persona)
            if maybe_persona is None:
                raise NotFoundPersonaException()
            return maybe_persona

        return self._try_catch(action)

    def delete_persona(self, persona_id: int) -> Persona:
        def action() -> Persona:
            self._validate_persona_id(persona_id)
            maybe_persona = self._persona_broker.delete_persona(persona_id)
            if maybe_persona is None:
                raise NotFoundPersonaException()
            return maybe_persona

        return self._try_catch(action)
