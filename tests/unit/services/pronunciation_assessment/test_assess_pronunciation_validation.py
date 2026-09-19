"""Unit tests for PronunciationAssessmentService.assess_pronunciation() -- rejected-input cases."""

import pytest

from api.models.foundations.pronunciation_assessment.exceptions import (
    InvalidPronunciationAssessmentRequestException,
    PronunciationAssessmentValidationException,
)
from api.services.foundations.pronunciation_assessment.pronunciation_assessment_service_validations import (
    MAX_REFERENCE_TEXT_LENGTH,
    MAX_WAV_BYTES,
)
from tests.unit.services.pronunciation_assessment.conftest import VALID_TEXT, VALID_WAV


class TestPronunciationAssessmentServiceAssessValidation:

    @pytest.mark.parametrize("bad_wav", [None, b""])
    def test_should_reject_empty_wav(self, service, mock_broker, bad_wav):
        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(bad_wav, VALID_TEXT)

        inner = exc_info.value.inner_exception
        assert isinstance(inner, InvalidPronunciationAssessmentRequestException)
        assert set(inner.errors) == {"wav_bytes"}
        mock_broker.assess.assert_not_called()

    def test_should_reject_oversized_wav(self, service, mock_broker):
        too_big = VALID_WAV + b"\x00" * MAX_WAV_BYTES

        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(too_big, VALID_TEXT)

        assert "wav_bytes" in exc_info.value.inner_exception.errors
        mock_broker.assess.assert_not_called()

    @pytest.mark.parametrize(
        "bad_wav",
        [b"not a wav file at all", b"RIFF\x00\x00\x00\x00AVI fmt ", b"XXXX\x00\x00\x00\x00WAVEfmt "],
    )
    def test_should_reject_non_wav_header(self, service, mock_broker, bad_wav):
        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(bad_wav, VALID_TEXT)

        assert "wav_bytes" in exc_info.value.inner_exception.errors
        mock_broker.assess.assert_not_called()

    @pytest.mark.parametrize("bad_text", [None, "", "   "])
    def test_should_reject_blank_reference_text(self, service, mock_broker, bad_text):
        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(VALID_WAV, bad_text)

        assert set(exc_info.value.inner_exception.errors) == {"reference_text"}
        mock_broker.assess.assert_not_called()

    def test_should_reject_too_long_reference_text(self, service, mock_broker):
        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(VALID_WAV, "a" * (MAX_REFERENCE_TEXT_LENGTH + 1))

        assert "reference_text" in exc_info.value.inner_exception.errors
        mock_broker.assess.assert_not_called()

    def test_should_batch_errors_for_every_bad_field(self, service, mock_broker):
        with pytest.raises(PronunciationAssessmentValidationException) as exc_info:
            service.assess_pronunciation(b"", "")

        assert set(exc_info.value.inner_exception.errors) == {"wav_bytes", "reference_text"}
        mock_broker.assess.assert_not_called()

    def test_should_accept_inputs_at_exactly_the_caps(self, service, mock_broker, assessment):
        # given
        at_cap_wav = VALID_WAV + b"\x00" * (MAX_WAV_BYTES - len(VALID_WAV))
        at_cap_text = "a" * MAX_REFERENCE_TEXT_LENGTH
        mock_broker.assess.return_value = assessment

        # when
        result = service.assess_pronunciation(at_cap_wav, at_cap_text)

        # then
        assert result is assessment
        mock_broker.assess.assert_called_once_with(at_cap_wav, at_cap_text)

    def test_should_log_the_validation_exception(self, service, mock_logging_broker):
        with pytest.raises(PronunciationAssessmentValidationException):
            service.assess_pronunciation(b"", VALID_TEXT)

        mock_logging_broker.log_error.assert_called_once()
        logged = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged) is PronunciationAssessmentValidationException
