"""Unit tests for D6 adaptive difficulty: the CEFR lookup and its composition
into the voice bot's system prompt. _compose_system_prompt's other inputs
(prompt file, scenario, profile read) are patched -- no DB, no files."""

from unittest.mock import Mock, patch

import pytest

from api.brokers.logging import LoggingBroker
from api.exposers import voice_conversation as vc
from api.models.foundations.learner_profile.exceptions import (
    LearnerProfileDependencyException,
    LearnerProfileValidationException,
    NotFoundLearnerProfileException,
)
from api.models.orchestrations.learner_profile.session_scenario import SessionScenario
from api.services.orchestrations.voice_conversation._difficulty import get_difficulty_block

BASE = "BASE\n\nFor this session, practice: SCENARIO\n\nPRESSURE"


class TestGetDifficultyBlock:

    @pytest.mark.parametrize("level", ["A1", "A2", "B1", "B2", "C1", "C2"])
    def test_should_return_block_mentioning_level_for_known_level(self, level):
        assert level in get_difficulty_block(level)

    def test_should_normalize_case_and_whitespace(self):
        assert get_difficulty_block("  b1 ") == get_difficulty_block("B1")

    @pytest.mark.parametrize("value", [None, "", "   ", "D9", "beginner"])
    def test_should_return_empty_for_missing_or_unknown(self, value):
        assert get_difficulty_block(value) == ""


def _compose(cefr):
    logging_broker = Mock(spec=LoggingBroker)
    with patch.object(vc, "FilePromptBroker") as prompt_broker, patch.object(
        vc, "_read_and_clear_scenario_override", return_value="SCENARIO"
    ) as override, patch.object(vc, "_load_scenario", return_value=None), patch.object(
        vc, "_read_cefr_estimate", return_value=cefr
    ) as read:
        prompt_broker.return_value.get_system_prompt.return_value = "BASE"
        result = vc._compose_system_prompt(logging_broker, "PRESSURE")
        override.assert_called_once_with()
        read.assert_called_once_with(logging_broker)
    return result


class TestComposeSystemPrompt:

    def test_should_append_difficulty_block_for_known_level(self):
        assert _compose("B2") == f"{BASE}\n\n{get_difficulty_block('B2')}"

    def test_should_leave_prompt_unchanged_when_estimate_is_none(self):
        assert _compose(None) == BASE

    def test_should_leave_prompt_unchanged_when_estimate_is_unknown(self):
        assert _compose("zzz") == BASE


class TestComposeSystemPromptVariant:

    def test_should_append_variant_block_before_difficulty_block(self):
        with patch.object(vc, "FilePromptBroker") as prompt_broker, patch.object(
            vc, "_read_and_clear_scenario_override", return_value="SCENARIO"
        ), patch.object(vc, "_load_scenario", return_value=None), patch.object(
            vc, "_read_cefr_estimate", return_value="B2"
        ):
            prompt_broker.return_value.get_system_prompt.return_value = "BASE"
            result = vc._compose_system_prompt(Mock(spec=LoggingBroker), "PRESSURE", "VARIANT")
        assert result == f"{BASE}\n\nVARIANT\n\n{get_difficulty_block('B2')}"
        prompt_broker.return_value.get_system_prompt.assert_called_once_with()


class TestScenarioTextProficiencyLine:
    SCENARIO = SessionScenario(proficiency_level="beginner", focus_category=None, suggested_topic="ser vs estar")

    def test_should_keep_proficiency_line_when_no_difficulty_block(self):
        assert vc._scenario_text(self.SCENARIO) == (
            "Speak at a beginner proficiency level. Focus this session on: ser vs estar."
        )

    def test_should_drop_proficiency_line_when_difficulty_block_present(self):
        assert vc._scenario_text(self.SCENARIO, has_difficulty_block=True) == "Focus this session on: ser vs estar."

    def test_should_drop_proficiency_line_from_composed_prompt_only_with_known_estimate(self):
        def compose(cefr):
            with patch.object(vc, "FilePromptBroker") as prompt_broker, patch.object(
                vc, "_read_and_clear_scenario_override", return_value=None
            ), patch.object(vc, "_load_scenario", return_value=self.SCENARIO), patch.object(
                vc, "_read_cefr_estimate", return_value=cefr
            ):
                prompt_broker.return_value.get_system_prompt.return_value = "BASE"
                return vc._compose_system_prompt(Mock(spec=LoggingBroker), "PRESSURE")

        assert "proficiency level" in compose(None)
        assert "proficiency level" in compose("zzz")
        assert "Speak at a beginner proficiency level." not in compose("B1")


class TestReadCefrEstimate:

    def test_should_return_none_when_profile_read_fails(self):
        logging_broker = Mock(spec=LoggingBroker)
        with patch.object(vc, "EnvConfigurationBroker") as config, patch.object(
            vc, "SqlAlchemyLearnerProfileBroker"
        ), patch.object(vc, "LearnerProfileService") as service:
            config.return_value.require.return_value = "postgresql://x"
            service.return_value.get_learner_profile.side_effect = LearnerProfileDependencyException(
                inner_exception=Exception("db down")
            )
            assert vc._read_cefr_estimate(logging_broker) is None
        logging_broker.log_warning.assert_called_once()

    def test_should_return_none_when_profile_missing(self):
        logging_broker = Mock(spec=LoggingBroker)
        with patch.object(vc, "EnvConfigurationBroker") as config, patch.object(
            vc, "SqlAlchemyLearnerProfileBroker"
        ), patch.object(vc, "LearnerProfileService") as service:
            config.return_value.require.return_value = "postgresql://x"
            service.return_value.get_learner_profile.side_effect = LearnerProfileValidationException(
                inner_exception=NotFoundLearnerProfileException()
            )
            assert vc._read_cefr_estimate(logging_broker) is None
            service.return_value.get_learner_profile.assert_called_once_with()
        logging_broker.log_warning.assert_called_once()

    def test_should_return_none_when_database_url_unset(self):
        logging_broker = Mock(spec=LoggingBroker)
        with patch.object(vc, "EnvConfigurationBroker") as config, patch.object(
            vc, "SqlAlchemyLearnerProfileBroker"
        ) as broker, patch.object(vc, "LearnerProfileService") as service:
            config.return_value.require.side_effect = KeyError("DATABASE_URL")
            assert vc._read_cefr_estimate(logging_broker) is None
            config.return_value.require.assert_called_once_with("DATABASE_URL")
            broker.assert_not_called()
            service.assert_not_called()
        logging_broker.log_warning.assert_called_once()

    def test_should_return_stored_estimate(self):
        with patch.object(vc, "EnvConfigurationBroker") as config, patch.object(
            vc, "SqlAlchemyLearnerProfileBroker"
        ), patch.object(vc, "LearnerProfileService") as service:
            config.return_value.require.return_value = "postgresql://x"
            service.return_value.get_learner_profile.return_value.cefr_estimate = "B1"
            assert vc._read_cefr_estimate(Mock(spec=LoggingBroker)) == "B1"
