"""Roleplay scenario library — LearnerProfile Phase 4.

Hand-authored, static (per decision record
Projects/spanish-companion/decisions/dynamic-bot-behavior-and-learner-memory.md,
Phase 4). Manual-pick-only for now — not tagged to a mistake category, so
suggest_session_scenario() is untouched by this. A scenario's `setting` is
injected into the composed prompt as the bot's role, usable both in
Conversation Mode (session topic) and Review Mode (structured practice).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RoleplayScenario:
    slug: str
    label: str
    setting: str


ROLEPLAY_SCENARIOS: list[RoleplayScenario] = [
    RoleplayScenario(
        slug="ordering_coffee",
        label="Ordering coffee",
        setting="You are a barista at a small café. The user is a customer ordering a drink and something to eat.",
    ),
    RoleplayScenario(
        slug="job_interview",
        label="Job interview",
        setting="You are an interviewer at a company. The user is a candidate interviewing for a job.",
    ),
    RoleplayScenario(
        slug="casual_chat",
        label="Casual chat",
        setting="You are a friend catching up with the user about their week, no particular topic.",
    ),
]


def get_roleplay_scenario(slug: str) -> RoleplayScenario | None:
    return next((s for s in ROLEPLAY_SCENARIOS if s.slug == slug), None)


if __name__ == "__main__":
    slugs = [s.slug for s in ROLEPLAY_SCENARIOS]
    assert len(slugs) == len(set(slugs)), f"duplicate slugs: {slugs}"
    assert get_roleplay_scenario("ordering_coffee") is not None
    assert get_roleplay_scenario("nonexistent") is None
    print("roleplay_scenarios self-check passed")
