"""Shared fixtures for PronunciationAssessmentService unit tests.

PronunciationAssessmentBroker is mocked via Mock(spec=...) -- no live Azure Speech SDK call.
"""

from unittest.mock import Mock

import pytest

from api.brokers.pronunciation_assessment import PronunciationAssessmentBroker
from api.models.foundations.pronunciation_assessment.pronunciation_assessment import (
    PhonemeScore,
    PronunciationAssessment,
    WordScore,
)
from api.services.foundations.pronunciation_assessment import PronunciationAssessmentService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

VALID_WAV = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 16
VALID_TEXT = "perro"


@pytest.fixture
def mock_broker():
    return Mock(spec=PronunciationAssessmentBroker)


@pytest.fixture
def service(mock_broker, mock_logging_broker):
    return PronunciationAssessmentService(mock_broker, logging_broker=mock_logging_broker)


@pytest.fixture
def assessment():
    return PronunciationAssessment(
        accuracy_score=90.0,
        fluency_score=80.0,
        completeness_score=100.0,
        pronunciation_score=88.0,
        prosody_score=None,
        words=[WordScore("perro", 90.0, "None", [PhonemeScore("p", 95.0)])],
    )
