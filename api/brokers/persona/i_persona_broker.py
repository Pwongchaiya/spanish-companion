"""Broker interface for `persona` persistence.

`typing.Protocol`, not `ABC`, per CLAUDE.md's Broker-interfaces waiver. Pure
CRUD only -- no upsert; find-or-create is higher-tier work built against this
interface. Mirrors api/brokers/pronunciation_result/i_pronunciation_result_broker.py,
with None-on-missing returns as in api/brokers/topic_covered/i_topic_covered_broker.py.
"""

from typing import Optional, Protocol

from api.models.foundations.persona.persona import Persona


class IPersonaBroker(Protocol):
    """External-resource boundary for `persona` persistence. Raw SQLAlchemy
    CRUD only -- no business logic, no exception handling. Lets
    sqlalchemy.exc.IntegrityError (unique slug) propagate unmodified."""

    def insert_persona(self, persona: Persona) -> Persona:
        """Insert one row from `persona` (its `id` is ignored) and return it
        with the assigned id."""
        ...

    def select_persona_by_id(self, persona_id: int) -> Optional[Persona]:
        """The row with this id, or None if it doesn't exist."""
        ...

    def select_persona_by_slug(self, slug: str) -> Optional[Persona]:
        """The row with this slug, or None if it doesn't exist."""
        ...

    def select_all_personas(self) -> list[Persona]:
        """Every row, ordered by `id` ascending."""
        ...

    def update_persona(self, persona: Persona) -> Optional[Persona]:
        """Overwrite slug/name/setting/memory/updated_at of the row whose id is
        `persona.id` and return it. None if that id doesn't exist."""
        ...

    def delete_persona(self, persona_id: int) -> Optional[Persona]:
        """Delete the row and return it as it was. None if it doesn't exist."""
        ...
