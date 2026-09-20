"""PersonaProcessingService: ensure_persona / get_persona_brief / update_memory happy paths."""

from dataclasses import replace

from api.data.personas import PERSONAS
from tests.unit.services.persona.persona_processing_helpers import NOW, OLD_TIME, make_persona, make_service, not_found


class TestPersonaProcessingServiceLogic:
    def test_ensure_returns_existing_row_without_create(self):
        service, foundation = make_service()
        row = make_persona()
        foundation.get_persona_by_slug.return_value = row

        assert service.ensure_persona("marta") is row

        foundation.get_persona_by_slug.assert_called_once_with("marta")
        foundation.create_persona.assert_not_called()

    def test_ensure_creates_from_static_definition_when_missing(self):
        service, foundation = make_service()
        foundation.get_persona_by_slug.side_effect = not_found()
        foundation.create_persona.side_effect = lambda p: p

        result = service.ensure_persona("don_luis")

        d = PERSONAS["don_luis"]
        assert (result.slug, result.name, result.setting, result.memory) == (d.slug, d.name, d.setting, None)
        assert result.id is None and result.updated_at == NOW
        foundation.create_persona.assert_called_once()

    def test_brief_omits_memory_section_when_memory_empty(self):
        service, foundation = make_service()
        foundation.get_persona_by_slug.return_value = make_persona(memory="  ")

        brief = service.get_persona_brief("marta")

        assert brief == "Marta\nA barista."
        assert "What you remember" not in brief

    def test_brief_includes_memory_section_when_present(self):
        service, foundation = make_service()
        foundation.get_persona_by_slug.return_value = make_persona(memory="Likes oat milk.")

        brief = service.get_persona_brief("marta")

        assert brief == "Marta\nA barista.\n\nWhat you remember from past chats:\nLikes oat milk."

    def test_update_memory_strips_and_stamps_clock_then_persists(self):
        service, foundation = make_service()
        row = make_persona()
        foundation.get_persona_by_slug.return_value = row
        foundation.update_persona.side_effect = lambda p: p

        result = service.update_memory("marta", "  Likes oat milk.  ")

        assert result == replace(row, memory="Likes oat milk.", updated_at=NOW)
        assert row.updated_at == OLD_TIME  # input row not mutated
        foundation.update_persona.assert_called_once_with(result)
        foundation.create_persona.assert_not_called()
