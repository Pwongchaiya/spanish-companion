"""Unit tests for D6 adaptive difficulty: the CEFR lookup and its composition
into the voice bot's system prompt. _compose_system_prompt's other inputs
(prompt file, scenario, profile read) are patched -- no DB, no files."""

from unittest.mock import Mock, patch

import pytest

from api.brokers.logging import LoggingBroker
from api.exposers import voice_conversation as vc
from api.models.foundations.learner_profile.exceptions import LearnerProfileDependencyException
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
    ) as override, patch.object(vc, "_read_cefr_estimate", return_value=cefr) as read:
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

    def test_should_return_stored_estimate(self):
        with patch.object(vc, "EnvConfigurationBroker") as config, patch.object(
            vc, "SqlAlchemyLearnerProfileBroker"
        ), patch.object(vc, "LearnerProfileService") as service:
            config.return_value.require.return_value = "postgresql://x"
            service.return_value.get_learner_profile.return_value.cefr_estimate = "B1"
            assert vc._read_cefr_estimate(Mock(spec=LoggingBroker)) == "B1"
