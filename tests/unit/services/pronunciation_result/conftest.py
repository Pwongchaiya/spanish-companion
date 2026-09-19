"""Shared fixtures for PronunciationResultService unit tests.

The broker is mocked via Mock(spec=IPronunciationResultBroker) at its Protocol
boundary. Every datetime is a fixed literal -- no datetime.now().
"""

from dataclasses import replace
from datetime import datetime
from unittest.mock import Mock

import pytest

from api.brokers.pronunciation_result import IPronunciationResultBroker
from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult
from api.services.foundations.pronunciation_result import PronunciationResultService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_TIME = datetime(2026, 1, 2, 10, 0, 0)


@pytest.fixture
def mock_pronunciation_result_broker():
    return Mock(spec=IPronunciationResultBroker)


@pytest.fixture
def service(mock_pronunciation_result_broker, mock_logging_broker):
    return PronunciationResultService(mock_pronunciation_result_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def make_result():
    def _make(**overrides) -> PronunciationResult:
        base = PronunciationResult(
            id=None,
            created_at=FIXED_TIME,
            reference_text="Buenos dias",
            accuracy_score=90.0,
            fluency_score=80.0,
            completeness_score=100.0,
            pronunciation_score=85.5,
            prosody_score=None,
            words_json=[{"word": "Buenos", "accuracy": 90.0}],
            locale="es-ES",
        )
        return replace(base, **overrides)

    return _make
