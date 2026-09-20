"""PersonaProcessingService: bad input is rejected before any Foundation write."""

import pytest

from api.models.foundations.persona.exceptions import InvalidPersonaException
from tests.unit.services.persona.persona_processing_helpers import make_service


class TestPersonaProcessingServiceValidation:
    @pytest.mark.parametrize("slug", ["", "nobody", None])
    def test_ensure_rejects_unknown_slug(self, slug):
        service, foundation = make_service()

        with pytest.raises(InvalidPersonaException) as caught:
            service.ensure_persona(slug)

        assert "slug" in caught.value.errors
        foundation.get_persona_by_slug.assert_not_called()
        foundation.create_persona.assert_not_called()

    @pytest.mark.parametrize("memory", [None, "", "   \n"])
    def test_update_memory_rejects_empty_memory(self, memory):
        service, foundation = make_service()

        with pytest.raises(InvalidPersonaException) as caught:
            service.update_memory("marta", memory)

        assert "memory" in caught.value.errors
        foundation.get_persona_by_slug.assert_not_called()
        foundation.update_persona.assert_not_called()
