"""Pre-session priming brief (A3): turns the learner's due mistake patterns
into one system-prompt block. Pure function, same shape as _pressure.py /
_difficulty.py. Seam for A4: add a sibling block function here (or a
`_x.py`) and append it in _compose_system_prompt.
"""

from typing import List

from api.models.orchestrations.learner_profile.session_scenario import DuePattern


def format_priming_brief(due: List[DuePattern]) -> str:
    """ "" when nothing is due; otherwise a one-line priority-review block."""
    if not due:
        return ""
    items = ", ".join(f"{p.category.replace('_', ' ')} (due {round(p.days_overdue)}d)" for p in due)
    return f"Priority review: {items}. Weave these in naturally; do not announce them."


def format_scene_constraints(constraints: List[str]) -> str:
    """A4: "" when none; otherwise the hard scene requirements, one per line."""
    if not constraints:
        return ""
    return "Scene requirements (mandatory, do not announce them):\n" + "\n".join(f"- {c}" for c in constraints)


if __name__ == "__main__":
    assert format_priming_brief([]) == ""
    one = format_priming_brief([DuePattern("past_tense", 4, 3.2)])
    assert one == "Priority review: past tense (due 3d). Weave these in naturally; do not announce them.", one
    two = format_priming_brief([DuePattern("ser_estar", 2, 0.0), DuePattern("gender", 1, 7.6)])
    assert "ser estar (due 0d), gender (due 8d)" in two
    assert format_scene_constraints([]) == ""
    assert format_scene_constraints(["a", "b"]).endswith("\n- a\n- b")
    print("OK")
