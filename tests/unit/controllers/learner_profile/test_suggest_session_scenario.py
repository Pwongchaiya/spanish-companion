"""Unit tests for LearnerProfileController.suggest_session_scenario().

Per CLAUDE.md's Phase 2 Layer-Agent Mapping: this in-process controller has
no HTTP response to map, so it gets Unit tier only (no Acceptance tests),
matching the now-deleted GenerationController/RetrievalController precedent
(tests/unit/controllers/generation/test_explain.py, git history). Unlike
that precedent, this controller does catch and re-raise its service's three
wrapper exceptions (see api/exposers/learner_profile.py's docstring), so
that pass-through behaviour is covered here too.
"""

from unittest.mock import Mock

import pytest

from api.exposers.learner_profile import LearnerProfileController
from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.orchestrations.learner_profile.i_learner_profile_orchestration_service import (
    LearnerProfileScenarioService,
)


@pytest.fixture
def mock_service():
    return Mock(spec=LearnerProfileScenarioService)


@pytest.fixture
def controller(mock_service):
    return LearnerProfileController(mock_service)


class TestSuggestSessionScenario:
    def test_should_return_service_result_unchanged(self, controller, mock_service):
        # given
        expected = SessionScenario(
            proficiency_level="intermediate",
            focus_category="verb_conjugation",
            suggested_topic="preterite-vs-imperfect",
            recent_mistake_categories=["verb_conjugation"],
        )
        mock_service.suggest_session_scenario.return_value = expected

        # when
        result = controller.suggest_session_scenario()

        # then
        assert result is expected

    def test_should_call_service_with_no_arguments(self, controller, mock_service):
        # given
        mock_service.suggest_session_scenario.return_value = SessionScenario(
            proficiency_level="beginner", focus_category=None, suggested_topic=None
        )

        # when
        controller.suggest_session_scenario()

        # then
        mock_service.suggest_session_scenario.assert_called_once_with()

    @pytest.mark.parametrize(
        "exception_type",
        [
            LearnerProfileOrchestrationValidationException,
            LearnerProfileOrchestrationDependencyException,
            LearnerProfileOrchestrationServiceException,
        ],
    )
    def test_should_reraise_orchestration_exception_unchanged(self, controller, mock_service, exception_type):
        # given
        raised = exception_type(inner_exception=Exception("boom"))
        mock_service.suggest_session_scenario.side_effect = raised

        # when / then
        with pytest.raises(exception_type) as exc_info:
            controller.suggest_session_scenario()
        assert exc_info.value is raised
