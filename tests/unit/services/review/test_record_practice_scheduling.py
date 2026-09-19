"""record_practice() wiring for A1: the judged grade is passed to record_review()."""

import pytest

from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException


class TestReviewOrchestratorRecordPracticeScheduling:

    @pytest.mark.parametrize("grade", ["again", "hard", "good", "easy"])
    def test_should_schedule_review_with_the_judged_grade(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_mistake_pattern_processing_service,
        mock_learner_profile_processing_service,
        make_flag,
        grade,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = grade

        # when
        result = service.record_practice("flag-1", "estoy cansado")

        # then
        assert result.grade == grade
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_mistake_pattern_processing_service.record_review.assert_called_once_with(profile.id, "ser_estar", grade)

    def test_should_not_raise_when_no_mistake_pattern_exists_to_schedule(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_mistake_pattern_processing_service,
        make_flag,
    ):
        # given -- mastered first try: resolve and record_review both find nothing
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="gender")
        mock_generation_service.judge_practice_attempt.return_value = "easy"
        mock_mistake_pattern_processing_service.resolve.side_effect = NotFoundMistakePatternException()
        mock_mistake_pattern_processing_service.record_review.side_effect = NotFoundMistakePatternException()

        # when
        result = service.record_practice("flag-1", "la mesa")

        # then
        assert result.mastered is True
        mock_mistake_pattern_processing_service.record_review.assert_called_once()
