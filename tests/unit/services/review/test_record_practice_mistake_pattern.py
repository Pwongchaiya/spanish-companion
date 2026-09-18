"""Unit tests for record_practice()'s LearnerProfile Phase 2 wiring: judging
the attempt and writing the verdict to mistake_pattern.

See decisions/dynamic-bot-behavior-and-learner-memory.md. Confirmed build-time
calls: one correct judged attempt marks a pattern resolved; a "still shaky"
verdict increments occurrence_count (record_occurrence is find-or-create, so
this also covers a category's first-ever occurrence).
"""

from api.models.foundations.mistake_pattern.exceptions import NotFoundMistakePatternException


class TestReviewOrchestratorRecordPracticeMistakePattern:

    def test_should_resolve_mistake_pattern_when_judge_says_mastered(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_mistake_pattern_processing_service,
        mock_learner_profile_processing_service,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = True

        # when
        result = service.record_practice("flag-1", "estoy cansado")

        # then
        assert result.mastered is True
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_mistake_pattern_processing_service.resolve.assert_called_once_with(profile.id, "ser_estar")
        mock_mistake_pattern_processing_service.record_occurrence.assert_not_called()

    def test_should_record_occurrence_when_judge_says_still_shaky(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_mistake_pattern_processing_service,
        mock_learner_profile_processing_service,
        make_flag,
    ):
        # given
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="ser_estar")
        mock_generation_service.judge_practice_attempt.return_value = False

        # when
        result = service.record_practice("flag-1", "soy cansado")

        # then
        assert result.mastered is False
        profile = mock_learner_profile_processing_service.ensure_profile.return_value
        mock_mistake_pattern_processing_service.record_occurrence.assert_called_once_with(profile.id, "ser_estar")
        mock_mistake_pattern_processing_service.resolve.assert_not_called()

    def test_should_not_raise_when_mastered_but_no_mistake_pattern_existed_yet(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        mock_mistake_pattern_processing_service,
        make_flag,
    ):
        # given -- first-ever practice attempt for a category, mastered on
        # the first try: nothing to resolve, and that's not a failure.
        mock_flag_service.get_flag.return_value = make_flag("flag-1", category="gender")
        mock_generation_service.judge_practice_attempt.return_value = True
        mock_mistake_pattern_processing_service.resolve.side_effect = NotFoundMistakePatternException()

        # when
        result = service.record_practice("flag-1", "la mesa")

        # then
        assert result.mastered is True

    def test_should_pass_flag_and_attempt_text_to_the_judge(
        self,
        service,
        mock_flag_service,
        mock_generation_service,
        make_flag,
    ):
        # given
        flag = make_flag("flag-1", category="gender")
        mock_flag_service.get_flag.return_value = flag
        mock_generation_service.judge_practice_attempt.return_value = True

        # when
        service.record_practice("flag-1", "la mesa")

        # then
        mock_generation_service.judge_practice_attempt.assert_called_once_with(flag, "la mesa")
