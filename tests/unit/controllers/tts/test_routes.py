"""Unit tests for the Tts Flask blueprint -- HTTP mapping only.

TtsService is mocked (Mock(spec=TtsService)): no real broker, no Azure
Speech SDK call. These tests verify only that the controller maps service
calls and exceptions onto the right HTTP status codes / body / headers.
Service logic itself already has its own unit tests at
tests/unit/services/tts/.
"""

from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.tts import make_tts_blueprint
from api.models.foundations.tts.exceptions import (
    InvalidTtsRequestException,
    TtsDependencyException,
    TtsServiceException,
    TtsUnavailableError,
    TtsValidationException,
)
from api.services.foundations.tts import TtsService


@pytest.fixture
def mock_service():
    return Mock(spec=TtsService)


@pytest.fixture
def client(mock_service):
    app = Flask(__name__)
    app.register_blueprint(make_tts_blueprint(mock_service))
    app.config["TESTING"] = True
    return app.test_client()


class TestTtsRoutesSynthesize:

    def test_should_return_200_and_wav_audio_when_synthesis_succeeds(self, client, mock_service):
        # given
        mock_service.synthesize_speech.return_value = b"RIFF....WAVEfmt "

        # when
        response = client.post("/tts/synthesize", json={"text": "perro"})

        # then
        assert response.status_code == 200
        assert response.mimetype == "audio/wav"
        assert response.data == b"RIFF....WAVEfmt "
        mock_service.synthesize_speech.assert_called_once_with("perro", 1.0)

    def test_should_pass_rate_from_the_body(self, client, mock_service):
        # given
        mock_service.synthesize_speech.return_value = b"audio"

        # when
        client.post("/tts/synthesize", json={"text": "perro", "rate": 0.6})

        # then
        mock_service.synthesize_speech.assert_called_once_with("perro", 0.6)

    def test_should_default_rate_to_one_when_absent(self, client, mock_service):
        # given
        mock_service.synthesize_speech.return_value = b"audio"

        # when
        client.post("/tts/synthesize", json={"text": "perro"})

        # then
        mock_service.synthesize_speech.assert_called_once_with("perro", 1.0)

    def test_should_pass_none_when_text_is_missing_from_body(self, client, mock_service):
        # given
        mock_service.synthesize_speech.side_effect = TtsValidationException(
            inner_exception=InvalidTtsRequestException()
        )

        # when
        client.post("/tts/synthesize", json={})

        # then
        mock_service.synthesize_speech.assert_called_once_with(None, 1.0)

    def test_should_return_400_when_validation_fails(self, client, mock_service):
        # given
        mock_service.synthesize_speech.side_effect = TtsValidationException(
            inner_exception=InvalidTtsRequestException()
        )

        # when
        response = client.post("/tts/synthesize", json={"text": ""})

        # then
        assert response.status_code == 400

    def test_should_return_500_when_dependency_fails(self, client, mock_service):
        # given
        mock_service.synthesize_speech.side_effect = TtsDependencyException(
            inner_exception=TtsUnavailableError("Azure Speech unreachable")
        )

        # when
        response = client.post("/tts/synthesize", json={"text": "perro"})

        # then
        assert response.status_code == 500

    def test_should_return_500_when_service_fails(self, client, mock_service):
        # given
        mock_service.synthesize_speech.side_effect = TtsServiceException(inner_exception=Exception("boom"))

        # when
        response = client.post("/tts/synthesize", json={"text": "perro"})

        # then
        assert response.status_code == 500
