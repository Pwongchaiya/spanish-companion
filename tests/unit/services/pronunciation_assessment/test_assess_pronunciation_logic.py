"""Unit tests for PronunciationAssessmentService.assess_pronunciation() -- happy path."""

from tests.unit.services.pronunciation_assessment.conftest import VALID_TEXT, VALID_WAV


class TestPronunciationAssessmentServiceAssessLogic:

    def test_should_return_broker_assessment_when_input_is_valid(self, service, mock_broker, assessment):
        # given
        mock_broker.assess.return_value = assessment

        # when
        result = service.assess_pronunciation(VALID_WAV, VALID_TEXT)

        # then
        assert result is assessment
        mock_broker.assess.assert_called_once_with(VALID_WAV, VALID_TEXT)

    def test_should_pass_reference_text_through_unmodified(self, service, mock_broker, assessment):
        # given
        mock_broker.assess.return_value = assessment

        # when
        service.assess_pronunciation(VALID_WAV, "¿Cómo estás?")

        # then
        mock_broker.assess.assert_called_once_with(VALID_WAV, "¿Cómo estás?")
