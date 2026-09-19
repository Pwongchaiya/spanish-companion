"""Unit tests for ProgressOrchestrationService's exception wrapping, per
progress_service_exceptions.py's three-tier _try_catch.

One representative failure point per dependency, exercised through
list_mistake_summary() (LearnerProfile/MistakePattern) and
list_topic_coverage() (LearnerProfile/TopicCovered) -- _try_catch wraps the
whole action() closure uniformly, so which dependency raised doesn't change
the wrapping behaviour under test, matching
test_suggest_session_scenario_exceptions.py's precedent.
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
from api.models.orchestrations.progress.exceptions import (
    ProgressOrchestrationDependencyException,
    ProgressOrchestrationServiceException,
    ProgressOrchestrationValidationException,
)


class TestProgressServiceExceptions:

    def test_should_raise_orchestration_validation_exception_when_learner_profile_service_raises_validation(
        self, service, mock_learner_profile_processing_service, mock_logging_broker
    ):
        # given
        leaf = LearnerProfileValidationException(inner_exception=NotFoundLearnerProfileException())
        mock_learner_profile_processing_service.ensure_profile.side_effect = leaf

        # when
        with pytest.raises(ProgressOrchestrationValidationException) as exc_info:
            service.list_mistake_summary()

        # then
        assert exc_info.value.inner_exception is leaf
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
        with pytest.raises(ProgressOrchestrationValidationException) as exc_info:
            service.list_mistake_summary()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_validation_exception_when_topic_covered_service_raises_validation(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_topic_covered_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        leaf = TopicCoveredValidationException(inner_exception=ValueError("bad profile_id"))
        mock_topic_covered_service.list_topic_covered_by_profile.side_effect = leaf

        # when
        with pytest.raises(ProgressOrchestrationValidationException) as exc_info:
            service.list_topic_coverage()

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
        with pytest.raises(ProgressOrchestrationDependencyException) as exc_info:
            service.list_mistake_summary()

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
        with pytest.raises(ProgressOrchestrationDependencyException) as exc_info:
            service.list_mistake_summary()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_dependency_exception_when_topic_covered_service_raises_dependency(
        self,
        service,
        mock_learner_profile_processing_service,
        mock_topic_covered_service,
        make_profile,
        mock_logging_broker,
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.return_value = make_profile(profile_id=1)
        leaf = TopicCoveredDependencyException(inner_exception=RuntimeError("storage down"))
        mock_topic_covered_service.list_topic_covered_by_profile.side_effect = leaf

        # when
        with pytest.raises(ProgressOrchestrationDependencyException) as exc_info:
            service.list_topic_coverage()

        # then
        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_service_exception_when_unexpected_error_occurs(
        self, service, mock_learner_profile_processing_service, mock_logging_broker
    ):
        # given
        mock_learner_profile_processing_service.ensure_profile.side_effect = ValueError("boom")

        # when
        with pytest.raises(ProgressOrchestrationServiceException):
            service.list_mistake_summary()

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
        with pytest.raises(ProgressOrchestrationServiceException):
            service.list_mistake_summary()

        # then
        mock_logging_broker.log_error.assert_called_once()


class TestGetLatestCompletedSessionExceptions:
    """get_latest_completed_session() (roadmap C2) shares _try_catch with
    every other Progress method -- one representative case per tier is
    enough, same call test_progress_service_exceptions.py already makes."""

    def test_should_raise_orchestration_dependency_exception_when_session_log_entry_service_raises_dependency(
        self, service, mock_session_log_entry_service, mock_logging_broker
    ):
        from api.models.foundations.session_log_entry.exceptions import SessionLogEntryDependencyException

        leaf = SessionLogEntryDependencyException(inner_exception=RuntimeError("storage down"))
        mock_session_log_entry_service.list_session_log_entries.side_effect = leaf

        with pytest.raises(ProgressOrchestrationDependencyException) as exc_info:
            service.get_latest_completed_session()

        assert exc_info.value.inner_exception is leaf
        mock_logging_broker.log_error.assert_called_once()

    def test_should_raise_orchestration_service_exception_when_unexpected_error_occurs(
        self, service, mock_session_log_entry_service, mock_logging_broker
    ):
        mock_session_log_entry_service.list_session_log_entries.side_effect = ValueError("boom")

        with pytest.raises(ProgressOrchestrationServiceException):
            service.get_latest_completed_session()

        mock_logging_broker.log_error.assert_called_once()
