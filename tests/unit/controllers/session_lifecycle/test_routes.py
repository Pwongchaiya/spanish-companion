"""Unit tests for the session_lifecycle Flask blueprint -- HTTP mapping only.

ConversationSessionService is mocked (Mock(spec=ConversationSessionService)):
no real broker, no real start/stop/graceful-escalation logic. These tests
verify only that the controller maps service calls and exceptions onto the
right HTTP status codes and JSON bodies. Service logic itself already has
its own unit tests at tests/unit/services/session_lifecycle/.
"""

from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.session_lifecycle import make_session_lifecycle_blueprint
from api.models.foundations.session_lifecycle.exceptions import (
    AlreadyRunningSessionException,
    NotRunningSessionException,
    SessionValidationException,
)
from api.models.foundations.session_lifecycle.session_status import SessionStatus
from api.services.foundations.session_lifecycle import SessionLifecycleService


@pytest.fixture
def mock_service():
    return Mock(spec=SessionLifecycleService)


@pytest.fixture
def client(mock_service):
    app = Flask(__name__)
    app.register_blueprint(make_session_lifecycle_blueprint(mock_service))
    app.config["TESTING"] = True
    return app.test_client()


class TestSessionLifecycleRoutesStart:

    def test_should_return_200_and_status_when_start_succeeds(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        response = client.post("/start")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"running": True, "ready": False, "graceful": None}
        mock_service.start.assert_called_once_with()
        mock_service.get_status.assert_called_once_with()

    def test_should_return_409_when_session_already_running(self, client, mock_service):
        # given
        mock_service.start.side_effect = SessionValidationException(inner_exception=AlreadyRunningSessionException())

        # when
        response = client.post("/start")

        # then
        assert response.status_code == 409
        assert response.get_json() == {"error": "A conversation session is already running"}
        mock_service.start.assert_called_once_with()
        mock_service.get_status.assert_not_called()


class TestSessionLifecycleRoutesStop:

    def test_should_return_200_and_status_when_stop_succeeds(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=False, ready=False, graceful=True)

        # when
        response = client.post("/stop")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"running": False, "ready": False, "graceful": True}
        mock_service.stop.assert_called_once_with()
        mock_service.get_status.assert_called_once_with()

    def test_should_return_404_when_session_not_running(self, client, mock_service):
        # given
        mock_service.stop.side_effect = SessionValidationException(inner_exception=NotRunningSessionException())

        # when
        response = client.post("/stop")

        # then
        assert response.status_code == 404
        assert response.get_json() == {"error": "No conversation session is running"}
        mock_service.stop.assert_called_once_with()
        mock_service.get_status.assert_not_called()


class TestSessionLifecycleRoutesStatus:

    def test_should_return_200_and_status(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=True, graceful=None)

        # when
        response = client.get("/status")

        # then
        assert response.status_code == 200
        assert response.get_json() == {"running": True, "ready": True, "graceful": None}
        mock_service.get_status.assert_called_once_with()
