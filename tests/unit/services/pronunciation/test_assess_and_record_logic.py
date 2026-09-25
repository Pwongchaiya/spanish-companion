"""Unit tests for PronunciationOrchestrationService.assess_and_record's happy path."""

from api.models.foundations.pronunciation_result.pronunciation_result import PronunciationResult
from tests.unit.services.pronunciation.conftest import FIXED_NOW, TEXT, WAV


class TestAssessAndRecordLogic:

    def test_should_assess_then_persist_and_return_stored_result(
        self, service, mock_assessment_service, mock_result_service, assessment, mock_logging_broker
    ):
        # given
        mock_assessment_service.assess_pronunciation.return_value = assessment

        # when
        result = service.assess_and_record(WAV, TEXT)

        # then
        assert result == PronunciationResult(
            id=None,
            created_at=FIXED_NOW,
            reference_text=TEXT,
            accuracy_score=90.0,
            fluency_score=80.0,
            completeness_score=100.0,
            pronunciation_score=88.0,
            prosody_score=None,
            words_json=[
                {
                    "word": "perro",
                    "accuracy": 90.0,
                    "error_type": "None",
                    "phonemes": [{"phoneme": "p", "accuracy": 95.0}, {"phoneme": "e", "accuracy": 85.0}],
                },
                {"word": "casa", "accuracy": None, "error_type": "Omission", "phonemes": []},
            ],
            locale="es-ES",
        )
        mock_assessment_service.assess_pronunciation.assert_called_once_with(WAV, TEXT)
        mock_result_service.create_pronunciation_result.assert_called_once_with(result)
        mock_logging_broker.log_info.assert_called_once()
        mock_logging_broker.log_error.assert_not_called()

    def test_should_persist_the_word_drill_flag(
        self, service, mock_assessment_service, mock_result_service, assessment
    ):
        # given
        mock_assessment_service.assess_pronunciation.return_value = assessment

        # when
        result = service.assess_and_record(WAV, TEXT, True)

        # then
        assert result.is_word_drill is True
        mock_assessment_service.assess_pronunciation.assert_called_once_with(WAV, TEXT)
        mock_result_service.create_pronunciation_result.assert_called_once_with(result)
