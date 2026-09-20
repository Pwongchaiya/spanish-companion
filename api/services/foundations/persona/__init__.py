"""Re-exports the concrete PersonaService class, declared directly in
persona_service.py (which inherits the Validations/Exceptions mixins by name)."""

from api.services.foundations.persona.i_persona_service import IPersonaService
from api.services.foundations.persona.persona_service import PersonaService

__all__ = [
    "IPersonaService",
    "PersonaService",
]
