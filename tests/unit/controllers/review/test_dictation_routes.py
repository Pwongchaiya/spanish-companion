"""HTTP mapping tests for the Review dictation routes (Phase 5 E2)."""

from unittest.mock import Mock

import pytest
from flask import Flask

from api.exposers.review import make_review_blueprint
from api.models.foundations.flag.exceptions import FlagValidationException, NotFoundFlagException
from api.models.orchestrations.review.dictation import DictationExercise, DictationResult, WordDiff
from api.models.orchestrations.review.exceptions import (
    ReviewOrchestrationServiceException,
    ReviewOrchestrationValidationException,
)
from api.services.orchestrations.review import ReviewOrchestrationService


@pytest.fixture
def mock_orchestrator():
    return Mock(spec=ReviewOrchestrationService)


@pytest.fixture
def client(mock_orchestrator):
    app = Flask(__name__)
    app.register_blueprint(make_review_blueprint(mock_orchestrator))
    return app.test_client()


class TestGetDictationExercise:

    def test_should_return_200_with_exercise(self, client, mock_orchestrator):
        mock_orchestrator.get_dictation_exercise.return_value = DictationExercise(flag_id="f1", target="él está")

        response = client.get("/review/dictation")

        assert response.status_code == 200
        assert response.get_json() == {"flag_id": "f1", "target": "él está"}
        mock_orchestrator.get_dictation_exercise.assert_called_once_with(None)

    def test_should_pass_exclude_query_param(self, client, mock_orchestrator):
        mock_orchestrator.get_dictation_exercise.return_value = DictationExercise(flag_id="f2", target="x")

        client.get("/review/dictation?exclude=f1")

        mock_orchestrator.get_dictation_exercise.assert_called_once_with("f1")

    def test_should_return_404_when_nothing_eligible(self, client, mock_orchestrator):
        mock_orchestrator.get_dictation_exercise.return_value = None

        response = client.get("/review/dictation")

        assert response.status_code == 404
        mock_orchestrator.get_dictation_exercise.assert_called_once_with(None)

    def test_should_return_500_on_service_exception(self, client, mock_orchestrator):
        mock_orchestrator.get_dictation_exercise.side_effect = ReviewOrchestrationServiceException(
            inner_exception=OSError("disk")
        )

        response = client.get("/review/dictation")

        assert response.status_code == 500
        mock_orchestrator.get_dictation_exercise.assert_called_once_with(None)


class TestCheckDictation:

    def test_should_return_200_with_result(self, client, mock_orchestrator):
        mock_orchestrator.check_dictation.return_value = DictationResult(
            flag_id="f1",
            target="él está",
            typed_text="el está",
            matches=False,
            words=[WordDiff("él", "el", "accent"), WordDiff("está", "está", "ok")],
        )

        response = client.post("/review/dictation/f1/check", json={"typed_text": "el está"})

        assert response.status_code == 200
        assert response.get_json() == {
            "flag_id": "f1",
            "target": "él está",
            "typed_text": "el está",
            "matches": False,
            "words": [
                {"target": "él", "typed": "el", "status": "accent"},
                {"target": "está", "typed": "está", "status": "ok"},
            ],
        }
        mock_orchestrator.check_dictation.assert_called_once_with("f1", "el está")

    @pytest.mark.parametrize("body", [{}, {"typed_text": None}, {"typed_text": "  "}, {"typed_text": 4}])
    def test_should_return_400_without_calling_orchestrator_on_bad_typed_text(self, client, mock_orchestrator, body):
        response = client.post("/review/dictation/f1/check", json=body)

        assert response.status_code == 400
        mock_orchestrator.check_dictation.assert_not_called()

    def test_should_return_404_when_flag_unknown(self, client, mock_orchestrator):
        mock_orchestrator.check_dictation.side_effect = ReviewOrchestrationValidationException(
            inner_exception=FlagValidationException(inner_exception=NotFoundFlagException("f1"))
        )

        response = client.post("/review/dictation/f1/check", json={"typed_text": "x"})

        assert response.status_code == 404
        mock_orchestrator.check_dictation.assert_called_once_with("f1", "x")

    def test_should_return_500_on_service_exception(self, client, mock_orchestrator):
        mock_orchestrator.check_dictation.side_effect = ReviewOrchestrationServiceException(
            inner_exception=RuntimeError("boom")
        )

        response = client.post("/review/dictation/f1/check", json={"typed_text": "x"})

        assert response.status_code == 500
        mock_orchestrator.check_dictation.assert_called_once_with("f1", "x")
