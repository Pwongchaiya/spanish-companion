"""Interface for the persona Processing service (typing.Protocol, per project convention)."""

from typing import Protocol

from api.models.foundations.persona.persona import Persona


class IPersonaProcessingService(Protocol):
    """External-facing contract for Persona's Processing service."""

    def ensure_persona(self, slug: str) -> Persona:
        """The DB row for slug, created from api/data/personas.py if absent.
        Unknown slug raises InvalidPersonaException. Other Foundation
        exceptions propagate unchanged."""
        ...

    def get_persona_brief(self, slug: str) -> str:
        """Prompt-ready text: name and setting, plus a "What you remember
        from past chats:" section only when memory is non-empty."""
        ...

    def update_memory(self, slug: str, memory: str) -> Persona:
        """Set the (stripped) memory and updated_at=clock() on the ensured
        row. Empty/None memory raises InvalidPersonaException before any
        Foundation call."""
        ...
