"""Unit tests for LearnerProfileOrchestrationService.suggest_session_scenario()
-- exception wrapping, per learner_profile_orchestration_service_exceptions.py's
three-tier _try_catch.

Validation and Dependency tiers each catch three leaf-wrapper classes (one per
LearnerProfile/MistakePattern/TopicCovered dependency); this file exercises one
representative failure point per class rather than every dependency's every
call site, since _try_catch wraps the whole action() closure uniformly -- which
dependency raised doesn't change the wrapping behaviour under test.

The three Foundation/Processing *ServiceException classes (LearnerProfile/
MistakePattern/TopicCoveredServiceException) are deliberately NOT caught by
name and must fall to the catch-all, per the exceptions mixin's own docstring
-- covered explicitly below, not just implied by the generic-Exception case.

No validation-shaped behaviour is orchestration-owned here (no input
parameters to suggest_session_scenario()), so there is no separate
_validation.py file -- validation-exception coverage lives in this file,
matching the skill's "fold into logic/exceptions" guidance.
"""

import pytest

from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileDependencyException,
    LearnerProfileServiceException,
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)
from api.models.foundations.mistake_pattern.exceptions import (
    MistakePatternDependencyException,
    MistakePatternServiceException,
    MistakePatternValidationException,
)
from api.models.foundations.topic_covered.exceptions import (
    TopicCoveredDependencyException,
    TopicCoveredServiceException,
    TopicCoveredValidationException,
)
from api.models.orchestrations.learner_profile.exceptions import (
    LearnerProfileOrchestrationDependencyException,
    LearnerProfileOrchestrationServiceException,
    LearnerProfileOrchestrationValidationException,
)


class TestSuggestSessionScenarioExceptions:

    def test_should_raise_orchestration_validation_exception_when_learner_profile_service_raises_validation(
        self, service, mock_learner_profile_processing_service, mock_logging_broker
    ):
        # given
        leaf = LearnerProfileValidationException(inner_exception=NotFoundLearnerProfileException())
        mock_learner_profile_processing_service.ensure_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationValidationException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_learner_profile_processing_service.ensure_profile.assert_called_once_with("beginner")
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_validation_exception_when_mistake_pattern_service_raises_validation(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        leaf = MistakePatternValidationException(inner_exception=ValueError("bad profile_id"))
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationValidationException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_validation_exception_when_topic_covered_service_raises_validation(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        leaf = TopicCoveredValidationException(inner_exception=ValueError("bad profile_id"))
        mock_topic_covered_service.list_topic_covered_by_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationValidationException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_dependency_exception_when_learner_profile_service_raises_dependency(
        self, service, mock_learner_profile_processing_service, mock_logging_broker
    ):
        # given
        leaf = LearnerProfileDependencyException(inner_exception=RuntimeError("storage down"))
        mock_learner_profile_processing_service.ensure_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationDependencyException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_dependency_exception_when_mistake_pattern_service_raises_dependency(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        leaf = MistakePatternDependencyException(inner_exception=RuntimeError("storage down"))
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationDependencyException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_dependency_exception_when_topic_covered_service_raises_dependency(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_mistake_pattern_service,
        mock_topic_covered_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        mock_mistake_pattern_service.list_mistake_patterns_by_profile.return_value = []
        leaf = TopicCoveredDependencyException(inner_exception=RuntimeError("storage down"))
        mock_topic_covered_service.list_topic_covered_by_profile.side_effect = leaf

        # when
        with pytest.raises(LearnerProfileOrchestrationDependencyException) as exc_info:
            service.suggest_session_scenario()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_service_exception_when_unexpected_error_occurs(
        self, service, mock_learner_profile_processing_service, mock_logging_broker
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.side_effect = ValueError("boom")

        # when
        with pytest.raises(LearnerProfileOrchestrationServiceException):
            service.suggest_session_scenario()

        # then
        mock_logging_broker.log_error.assert_called_once()

    @pytest.mark.parametrize(
        "leaf_exception_class",
        [
            LearnerProfileServiceException,
            MistakePatternServiceException,
            TopicCoveredServiceException,
        ],
    )
    def test_should_raise_orchestration_service_exception_when_a_foundation_service_exception_is_not_caught_by_name(
        self, service, mock_learner_profile_processing_service, mock_logging_broker, leaf_exception_class
    ):
        # given -- LearnerProfile/MistakePattern/TopicCoveredServiceException are
        # deliberately absent from the validation/dependency except clauses, so
        # each must fall through to the catch-all tier, not go unwrapped.
        mock_learner_profile_processing_service.ensure_profile.side_effect = leaf_exception_class(
            inner_exception=RuntimeError("unexpected")
        )

        # when
        with pytest.raises(LearnerProfileOrchestrationServiceException):
            service.suggest_session_scenario()

        # then
        mock_logging_broker.log_error.assert_called_once()
