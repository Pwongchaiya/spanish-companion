"""Shared fixtures for PersonaService unit tests.

The broker is mocked via Mock(spec=IPersonaBroker) at its Protocol boundary.
Every datetime is a fixed literal -- no datetime.now().
"""

from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.persona import IPersonaBroker
from api.models.foundations.persona.persona import Persona
from api.services.foundations.persona import PersonaService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_TIME = datetime(2026, 1, 2, 10, 0, 0)


@pytest.fixture
def mock_persona_broker():
    return Mock(spec=IPersonaBroker)


@pytest.fixture
def service(mock_persona_broker, mock_logging_broker):
    return PersonaService(mock_persona_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_persona():
    def _make(**overrides) -> Persona:
        base = Persona(
            id=None,
            slug="cafe",
            name="Lucia",
            setting="A busy cafe in Madrid",
            memory=None,
            updated_at=FIXED_TIME,
        )
        return replace(base, **overrides)

    return _make
