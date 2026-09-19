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

from api.exposers.learner_profile import LearnerProfileController
from api.exposers.session_lifecycle import make_session_lifecycle_blueprint
from api.models.foundations.session_lifecycle.exceptions import (
    AlreadyRunningSessionException,
    NotRunningSessionException,
    SessionValidationException,
)
from api.models.foundations.session_lifecycle.session_status import SessionStatus
from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.foundations.session_lifecycle import SessionLifecycleService


@pytest.fixture
def mock_service():
    return Mock(spec=SessionLifecycleService)


@pytest.fixture
def mock_learner_profile_controller():
    return Mock(spec=LearnerProfileController)


@pytest.fixture
def client(mock_service, mock_learner_profile_controller):
    app = Flask(__name__)
    app.register_blueprint(make_session_lifecycle_blueprint(mock_service, mock_learner_profile_controller))
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
        mock_service.start.assert_called_once_with(None, None, None, None)
        mock_service.get_status.assert_called_once_with()

    def test_should_pass_scenario_text_from_body_through_to_service(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post("/start", json={"scenario_text": "practice ordering coffee"})

        # then
        mock_service.start.assert_called_once_with("practice ordering coffee", None, None, None)

    def test_should_fold_session_length_hint_into_scenario_text(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post(
            "/start",
            json={"scenario_text": "practice ordering coffee", "session_length_hint": "5"},
        )

        # then
        mock_service.start.assert_called_once_with(
            "practice ordering coffee Aim for about a 5-minute conversation.", None, None, None
        )

    def test_should_pass_session_length_hint_alone_when_no_scenario_text(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post("/start", json={"session_length_hint": "20"})

        # then
        mock_service.start.assert_called_once_with("Aim for about a 20-minute conversation.", None, None, None)

    def test_should_pass_pressure_level_from_body_through_to_service(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post("/start", json={"pressure_level": "push"})

        # then
        mock_service.start.assert_called_once_with(None, "push", None, None)

    def test_should_return_400_when_pressure_level_is_invalid(self, client, mock_service):
        # when
        response = client.post("/start", json={"pressure_level": "extreme"})

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid pressure_level: 'extreme'"}
        mock_service.start.assert_not_called()

    def test_should_pass_variant_from_body_through_to_service(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post("/start", json={"variant": "rioplatense"})

        # then
        mock_service.start.assert_called_once_with(None, None, "rioplatense", None)

    def test_should_return_400_when_variant_is_invalid(self, client, mock_service):
        # when
        response = client.post("/start", json={"variant": "klingon"})

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid variant: 'klingon'"}
        mock_service.start.assert_not_called()

    def test_should_return_409_when_session_already_running(self, client, mock_service):
        # given
        mock_service.start.side_effect = SessionValidationException(inner_exception=AlreadyRunningSessionException())

        # when
        response = client.post("/start")

        # then
        assert response.status_code == 409
        assert response.get_json() == {"error": "A conversation session is already running"}
        mock_service.start.assert_called_once_with(None, None, None, None)
        mock_service.get_status.assert_not_called()


class TestSessionLifecycleRoutesSessionScenario:

    def test_should_return_200_and_scenario_when_suggestion_succeeds(self, client, mock_learner_profile_controller):
        # given
        mock_learner_profile_controller.suggest_session_scenario.return_value = SessionScenario(
            proficiency_level="beginner",
            focus_category="gender_agreement",
            suggested_topic="gender_agreement",
            recent_mistake_categories=["gender_agreement"],
        )

        # when
        response = client.get("/session-scenario")

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "proficiency_level": "beginner",
            "focus_category": "gender_agreement",
            "suggested_topic": "gender_agreement",
            "recent_mistake_categories": ["gender_agreement"],
            "due_patterns": [],
            "boss_fight_text": None,
            "boss_fight_categories": [],
        }
        mock_learner_profile_controller.suggest_session_scenario.assert_called_once_with()

    def test_should_return_400_when_validation_fails(self, client, mock_learner_profile_controller):
        # given
        mock_learner_profile_controller.suggest_session_scenario.side_effect = (
            LearnerProfileOrchestrationValidationException(inner_exception=Exception("bad state"))
        )

        # when
        response = client.get("/session-scenario")

        # then
        assert response.status_code == 400

    def test_should_return_500_when_dependency_fails(self, client, mock_learner_profile_controller):
        # given
        mock_learner_profile_controller.suggest_session_scenario.side_effect = (
            LearnerProfileOrchestrationDependencyException(inner_exception=Exception("db down"))
        )

        # when
        response = client.get("/session-scenario")

        # then
        assert response.status_code == 500

    def test_should_return_500_when_service_fails(self, client, mock_learner_profile_controller):
        # given
        mock_learner_profile_controller.suggest_session_scenario.side_effect = (
            LearnerProfileOrchestrationServiceException(inner_exception=Exception("boom"))
        )

        # when
        response = client.get("/session-scenario")

        # then
        assert response.status_code == 500


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

    def test_should_pass_scenario_slug_from_body_through_to_service(self, client, mock_service):
        # given
        mock_service.get_status.return_value = SessionStatus(running=True, ready=False, graceful=None)

        # when
        client.post("/start", json={"scenario_slug": "ordering_coffee"})

        # then
        mock_service.start.assert_called_once_with(None, None, None, "ordering_coffee")

    def test_should_return_400_when_scenario_slug_is_unknown(self, client, mock_service):
        # when
        response = client.post("/start", json={"scenario_slug": "nope"})

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid scenario_slug: 'nope'"}
        mock_service.start.assert_not_called()
