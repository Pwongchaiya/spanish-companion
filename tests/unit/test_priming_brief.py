"""A3 priming brief: format_priming_brief and its composition into the bot prompt."""

from unittest.mock import Mock, patch

from api.brokers.logging import LoggingBroker
from api.exposers import voice_conversation as vc
from api.models.orchestrations.learner_profile.session_scenario import DuePattern, SessionScenario
from api.services.orchestrations.voice_conversation._priming import format_priming_brief

BASE = "BASE\n\nFor this session, practice: {}\n\nPRESSURE"
BRIEF = "Priority review: past tense (due 3d). Weave these in naturally; do not announce them."
SCENARIO = SessionScenario("beginner", None, None, due_patterns=[DuePattern("past_tense", 2, 3.2)])


def test_format_priming_brief_empty_and_populated():
    assert format_priming_brief([]) == ""
    assert format_priming_brief(SCENARIO.due_patterns) == BRIEF


def _compose(override, scenario=None, load_side_effect=None):
    lb = Mock(spec=LoggingBroker)
    with patch.object(vc, "FilePromptBroker") as pb, patch.object(
        vc, "_read_and_clear_scenario_override", return_value=override
    ), patch.object(vc, "_load_scenario", return_value=scenario, side_effect=load_side_effect), patch.object(
        vc, "_read_cefr_estimate", return_value=None
    ):
        pb.return_value.get_system_prompt.return_value = "BASE"
        return vc._compose_system_prompt(lb, "PRESSURE")


def test_brief_appended_on_override_path_and_override_wins_scenario_line():
    assert _compose("MINE", SCENARIO) == f"{BASE.format('MINE')}\n\n{BRIEF}"


def test_brief_appended_on_default_path():
    out = _compose(None, SCENARIO)
    assert out.endswith(BRIEF) and "Speak at a beginner proficiency level." in out


def test_degrades_to_no_brief_when_scenario_unavailable_or_load_raises():
    assert _compose("MINE", None) == BASE.format("MINE")
    assert _compose("MINE", load_side_effect=RuntimeError("boom")) == BASE.format("MINE")
