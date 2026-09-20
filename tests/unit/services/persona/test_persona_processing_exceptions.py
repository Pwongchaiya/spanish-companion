"""PersonaProcessingService: Foundation exceptions propagate unchanged."""

import pytest

from api.models.foundations.persona.exceptions import (
    InvalidPersonaException,
    PersonaDependencyException,
    PersonaValidationException,
)
from tests.unit.services.persona.persona_processing_helpers import make_persona, make_service


class TestPersonaProcessingServiceExceptions:
    def test_ensure_propagates_dependency_exception_from_get(self):
        service, foundation = make_service()
        expected = PersonaDependencyException(inner_exception=Exception("db down"))
        foundation.get_persona_by_slug.side_effect = expected

        with pytest.raises(PersonaDependencyException) as caught:
            service.ensure_persona("marta")

        assert caught.value is expected
        foundation.create_persona.assert_not_called()

    def test_ensure_reraises_non_not_found_validation_exception(self):
        service, foundation = make_service()
        expected = PersonaValidationException(inner_exception=InvalidPersonaException())
        foundation.get_persona_by_slug.side_effect = expected

        with pytest.raises(PersonaValidationException) as caught:
            service.ensure_persona("marta")

        assert caught.value is expected
        foundation.create_persona.assert_not_called()

    def test_update_memory_propagates_dependency_exception_from_update(self):
        service, foundation = make_service()
        foundation.get_persona_by_slug.return_value = make_persona()
        expected = PersonaDependencyException(inner_exception=Exception("db down"))
        foundation.update_persona.side_effect = expected

        with pytest.raises(PersonaDependencyException) as caught:
            service.update_memory("marta", "hi")

        assert caught.value is expected
        foundation.update_persona.assert_called_once()
