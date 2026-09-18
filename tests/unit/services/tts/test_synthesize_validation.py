"""Unit tests for TtsService.synthesize_speech() -- rejected-input cases.

Mirrors the topic_covered precedent
(tests/unit/services/topic_covered/test_topic_covered_service.py):
InvalidTtsRequestException batches every failing field before
TtsService wraps it into TtsValidationException.
"""

import pytest

from api.models.foundations.tts.exceptions import InvalidTtsRequestException, TtsValidationException
from api.services.foundations.tts.tts_service_validations import MAX_TEXT_LENGTH


class TestTtsServiceSynthesizeValidation:

    @pytest.mark.parametrize("bad_text", [None, "", "   "])
    def test_should_raise_validation_exception_when_text_is_blank(self, service, mock_broker, bad_text):
        # when
        with pytest.raises(TtsValidationException) as exc_info:
            service.synthesize_speech(bad_text)

        # then
        assert isinstance(exc_info.value.inner_exception, InvalidTtsRequestException)
        assert "text" in exc_info.value.inner_exception.errors
        mock_broker.synthesize.assert_not_called()

    def test_should_raise_validation_exception_when_text_is_too_long(self, service, mock_broker):
        # given
        too_long = "a" * (MAX_TEXT_LENGTH + 1)

        # when
        with pytest.raises(TtsValidationException) as exc_info:
            service.synthesize_speech(too_long)

        # then
        assert isinstance(exc_info.value.inner_exception, InvalidTtsRequestException)
        assert "text" in exc_info.value.inner_exception.errors
        mock_broker.synthesize.assert_not_called()

    def test_should_accept_text_at_exactly_the_length_cap(self, service, mock_broker):
        # given
        at_cap = "a" * MAX_TEXT_LENGTH
        mock_broker.synthesize.return_value = b"audio"

        # when
        result = service.synthesize_speech(at_cap)

        # then
        assert result == b"audio"
        mock_broker.synthesize.assert_called_once_with(at_cap)

    def test_should_log_the_validation_exception(self, service, mock_broker, mock_logging_broker):
        # when
        with pytest.raises(TtsValidationException):
            service.synthesize_speech("")

        # then
        mock_logging_broker.log_error.assert_called_once()
        logged_exception = mock_logging_broker.log_error.call_args.args[0]
        assert type(logged_exception) is TtsValidationException
