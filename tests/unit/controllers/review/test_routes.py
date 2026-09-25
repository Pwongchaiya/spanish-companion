"""Unit tests for the Review blueprint's HTTP mapping.

Per CLAUDE.md's Phase 2 test strategy and the Exposer Agent's waivers: this
tier verifies HTTP mapping only (status codes, JSON shape, isoformat
timestamps, FlagNotFoundException -> 404, attempt_text validation -> 400
before the orchestrator is ever called) -- never Review's actual flow logic.
ReviewOrchestrationService is mocked via unittest.mock.Mock(spec=ReviewOrchestrationService);
tests/unit/services/review/ (a parallel dispatch) covers the real logic.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask

from api.brokers.practice_log import PracticeAttempt
from api.exposers.review import make_review_blueprint
from api.models.orchestrations.review.practice_result import PracticeResult
from api.models.orchestrations.review.task_outcome import TaskOutcome
from api.models.foundations.flag import Flag
from api.models.foundations.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.orchestrations.review.exceptions import (
    ReviewOrchestrationDependencyException,
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from api.services.orchestrations.review import ReviewOrchestrationService
from rag.models.foundations.generation import Explanation


@pytest.fixture
def mock_orchestrator():
    return Mock(spec=ReviewOrchestrationService)


@pytest.fixture
def client(mock_orchestrator):
    app = Flask(__name__)
    app.register_blueprint(make_review_blueprint(mock_orchestrator))
    return app.test_client()


@pytest.fixture
def flag():
    return Flag(
        id="flag-1",
        said="yo soy tener",
        corrected="yo tengo",
        category="verb_conjugation",
        timestamp=datetime(2026, 8, 1, 12, 0, 0),
    )


class TestListFlags:

    def test_should_return_200_with_isoformat_timestamp_when_flags_exist(self, client, mock_orchestrator, flag):
        # given
        mock_orchestrator.list_flags.return_value = [flag]

        # when
        response = client.get("/review/flags")

        # then
        assert response.status_code == 200
        body = response.get_json()
        assert body == [
            {
                "id": "flag-1",
                "said": "yo soy tener",
                "corrected": "yo tengo",
                "category": "verb_conjugation",
                "timestamp": "2026-08-01T12:00:00",
                "channel": "grammar",
                "occurrence_count": 1,
                "status": "open",
            }
        ]
        assert isinstance(body[0]["timestamp"], str)
        mock_orchestrator.list_flags.assert_called_once_with()

    def test_should_return_200_with_empty_list_when_no_flags(self, client, mock_orchestrator):
        # given
        mock_orchestrator.list_flags.return_value = []

        # when
        response = client.get("/review/flags")

        # then
        assert response.status_code == 200
        assert response.get_json() == []

    # H7: this route had no try/except at all, so a failure below reached
    # Flask raw and answered with an unmapped 500 plus a traceback.
    def test_should_return_500_when_orchestrator_raises_service_exception(self, client, mock_orchestrator):
        # given
        leaf = OSError("disk read failed")
        mock_orchestrator.list_flags.side_effect = ReviewOrchestrationServiceException(inner_exception=leaf)

        # when
        response = client.get("/review/flags")

        # then
        assert response.status_code == 500
        assert response.get_json() == {"error": str(leaf)}

    def test_should_return_500_when_orchestrator_raises_dependency_exception(self, client, mock_orchestrator):
        # given
        leaf = OSError("disk read failed")
        mock_orchestrator.list_flags.side_effect = ReviewOrchestrationDependencyException(inner_exception=leaf)

        # when
        response = client.get("/review/flags")

        # then
        assert response.status_code == 500
        assert response.get_json() == {"error": str(leaf)}


class TestExplainFlag:

    def test_should_return_200_with_explanation_when_flag_found(self, client, mock_orchestrator):
        # given
        mock_orchestrator.explain_flag.return_value = Explanation(
            explanation="Use 'tengo' for the first person present of tener.",
            source_url="https://rae.es/some-topic",
            source_excerpt="El verbo 'tener' se conjuga como 'tengo' en la primera persona.",
        )

        # when
        response = client.get("/review/flags/flag-1/explain")

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "explanation": "Use 'tengo' for the first person present of tener.",
            "source_url": "https://rae.es/some-topic",
            "source_excerpt": "El verbo 'tener' se conjuga como 'tengo' en la primera persona.",
        }
        mock_orchestrator.explain_flag.assert_called_once_with("flag-1")

    def test_should_return_404_with_error_body_when_flag_not_found(self, client, mock_orchestrator):
        # given -- mirrors the real orchestrator's wrap depth: the leaf sits
        # two levels deep, at inner_exception.inner_exception
        mock_orchestrator.explain_flag.side_effect = ReviewOrchestrationValidationException(
            inner_exception=FlagValidationException(inner_exception=NotFoundFlagException("flag-1"))
        )

        # when
        response = client.get("/review/flags/flag-1/explain")

        # then -- body comes from str(e.inner_exception), the FlagValidationException
        # wrapper's own message, not the leaf's -- controller response-body logic is
        # untouched by this wave, see api/exposers/review.py
        assert response.status_code == 404
        assert response.get_json() == {"error": "Flag validation error occurred. Fix the errors and try again."}


class TestRecordPractice:

    def test_should_return_201_with_isoformat_timestamp_when_practice_recorded(self, client, mock_orchestrator):
        # given
        mock_orchestrator.record_practice.return_value = PracticeResult(
            attempt=PracticeAttempt(
                flag_id="flag-1",
                attempt_text="yo tengo",
                timestamp=datetime(2026, 8, 1, 12, 5, 0),
                grade="good",
            ),
            mastered=True,
            grade="good",
        )

        # when
        response = client.post("/review/flags/flag-1/practice", json={"attempt_text": "yo tengo"})

        # then
        assert response.status_code == 201
        body = response.get_json()
        assert body == {
            "flag_id": "flag-1",
            "attempt_text": "yo tengo",
            "timestamp": "2026-08-01T12:05:00",
            "mastered": True,
            "grade": "good",
        }
        assert isinstance(body["timestamp"], str)
        mock_orchestrator.record_practice.assert_called_once_with("flag-1", "yo tengo", None)

    def test_should_pass_a_known_roleplay_slug_through_to_the_orchestrator(self, client, mock_orchestrator):
        # given
        mock_orchestrator.record_practice.return_value = PracticeResult(
            attempt=PracticeAttempt(
                flag_id="flag-1",
                attempt_text="yo tengo",
                timestamp=datetime(2026, 8, 1, 12, 5, 0),
                grade="good",
            ),
            mastered=True,
            grade="good",
        )

        # when
        response = client.post(
            "/review/flags/flag-1/practice",
            json={"attempt_text": "yo tengo", "roleplay_slug": "ordering_coffee"},
        )

        # then
        assert response.status_code == 201
        mock_orchestrator.record_practice.assert_called_once_with("flag-1", "yo tengo", "ordering_coffee")

    def test_should_return_400_without_calling_orchestrator_when_roleplay_slug_unknown(self, client, mock_orchestrator):
        # when
        response = client.post(
            "/review/flags/flag-1/practice",
            json={"attempt_text": "yo tengo", "roleplay_slug": "not_a_real_scenario"},
        )

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid roleplay_slug: 'not_a_real_scenario'"}
        mock_orchestrator.record_practice.assert_not_called()

    def test_should_return_404_with_error_body_when_flag_not_found(self, client, mock_orchestrator):
        # given -- mirrors the real orchestrator's wrap depth: the leaf sits
        # two levels deep, at inner_exception.inner_exception
        mock_orchestrator.record_practice.side_effect = ReviewOrchestrationValidationException(
            inner_exception=FlagValidationException(inner_exception=NotFoundFlagException("flag-1"))
        )

        # when
        response = client.post("/review/flags/flag-1/practice", json={"attempt_text": "yo tengo"})

        # then -- body comes from str(e.inner_exception), the FlagValidationException
        # wrapper's own message, not the leaf's -- controller response-body logic is
        # untouched by this wave, see api/exposers/review.py
        assert response.status_code == 404
        assert response.get_json() == {"error": "Flag validation error occurred. Fix the errors and try again."}

    @pytest.mark.parametrize(
        "body",
        [
            {},  # missing attempt_text entirely
            {"attempt_text": None},  # explicit null
            {"attempt_text": "   "},  # blank string
            {"attempt_text": 42},  # non-string
        ],
        ids=["missing", "null", "blank", "non-string"],
    )
    def test_should_return_400_without_calling_orchestrator_when_attempt_text_invalid(
        self, client, mock_orchestrator, body
    ):
        # when
        response = client.post("/review/flags/flag-1/practice", json=body)

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "attempt_text is required"}
        mock_orchestrator.record_practice.assert_not_called()

    def test_should_return_400_not_500_when_no_json_body_sent(self, client, mock_orchestrator):
        # when -- no json=, no data=, no Content-Type at all
        response = client.post("/review/flags/flag-1/practice")

        # then
        assert response.status_code == 400
        assert response.get_json() == {"error": "attempt_text is required"}
        mock_orchestrator.record_practice.assert_not_called()


class TestTaskOutcomeRoute:

    def test_should_return_outcome_json(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_task_outcome.return_value = TaskOutcome(
            scenario_slug="ordering_coffee", label="Ordering coffee", success_condition="orders both", outcome="success"
        )

        # when
        response = client.get("/review/task-outcome")

        # then
        assert response.status_code == 200
        assert response.get_json() == {
            "scenario_slug": "ordering_coffee",
            "label": "Ordering coffee",
            "success_condition": "orders both",
            "outcome": "success",
        }
        mock_orchestrator.get_task_outcome.assert_called_once_with()

    def test_should_return_null_when_no_task_session(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_task_outcome.return_value = None

        # when
        response = client.get("/review/task-outcome")

        # then
        assert response.status_code == 200
        assert response.get_json() is None

    def test_should_return_500_on_service_exception(self, client, mock_orchestrator):
        # given
        mock_orchestrator.get_task_outcome.side_effect = ReviewOrchestrationServiceException(
            inner_exception=RuntimeError("boom")
        )

        # when
        response = client.get("/review/task-outcome")

        # then
        assert response.status_code == 500
