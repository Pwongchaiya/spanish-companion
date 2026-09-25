"""Unit tests for TtsService.synthesize_speech() -- happy path.

See test_synthesize_validation.py for the rejected-input cases and
test_synthesize_exceptions.py for the broker-failure case.
"""


class TestTtsServiceSynthesize:

    def test_should_return_broker_bytes_when_text_is_valid(self, service, mock_broker):
        # given
        mock_broker.synthesize.return_value = b"RIFF....WAVEfmt "

        # when
        result = service.synthesize_speech("perro")

        # then
        assert result == b"RIFF....WAVEfmt "
        mock_broker.synthesize.assert_called_once_with("perro", 1.0)

    def test_should_pass_text_through_unmodified(self, service, mock_broker):
        # given
        mock_broker.synthesize.return_value = b"audio"

        # when
        service.synthesize_speech("¿Cómo estás?")

        # then
        mock_broker.synthesize.assert_called_once_with("¿Cómo estás?", 1.0)

    def test_should_pass_rate_through_to_the_broker(self, service, mock_broker):
        # given
        mock_broker.synthesize.return_value = b"audio"

        # when
        service.synthesize_speech("perro", 0.6)

        # then
        mock_broker.synthesize.assert_called_once_with("perro", 0.6)
