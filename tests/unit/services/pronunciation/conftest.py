"""Shared fixtures for PronunciationOrchestrationService unit tests.

Both Foundation dependencies are mocked via Mock(spec=...) at their Protocol
boundary; the clock is fixed so created_at is deterministic.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from api.models.foundations.pronunciation_assessment.pronunciation_assessment import (
    PhonemeScore,
    PronunciationAssessment,
    WordScore,
)
from api.services.foundations.pronunciation_assessment import IPronunciationAssessmentService
from api.services.foundations.pronunciation_result import IPronunciationResultService
from api.services.orchestrations.pronunciation import PronunciationOrchestrationService
from tests.unit.services._api_logging_fixture import mock_logging_broker  # noqa: F401

FIXED_NOW = datetime(2026, 1, 2, 3, 4, 5)
WAV = b"RIFF\x00\x00\x00\x00WAVEfmt " + b"\x00" * 40
TEXT = "perro"


@pytest.fixture
def mock_assessment_service():
    return Mock(spec=IPronunciationAssessmentService)


@pytest.fixture
def mock_result_service():
    service = Mock(spec=IPronunciationResultService)
    service.create_pronunciation_result.side_effect = lambda result: result
    return service


@pytest.fixture
def service(mock_assessment_service, mock_result_service, mock_logging_broker):
    return PronunciationOrchestrationService(
        mock_assessment_service,
        mock_result_service,
        clock=lambda: FIXED_NOW,
        logging_broker=mock_logging_broker,
    )


@pytest.fixture
def assessment():
    return PronunciationAssessment(
        accuracy_score=90.0,
        fluency_score=80.0,
        completeness_score=100.0,
        pronunciation_score=88.0,
        prosody_score=None,
        words=[
            WordScore("perro", 90.0, "None", [PhonemeScore("p", 95.0), PhonemeScore("e", 85.0)]),
            WordScore("casa", None, "Omission", []),
        ],
    )
