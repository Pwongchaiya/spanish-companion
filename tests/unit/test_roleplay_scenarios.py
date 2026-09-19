from api.data.roleplay_scenarios import ROLEPLAY_SCENARIOS, SCENARIO_TIERS


def test_every_scenario_has_valid_tier() -> None:
    assert ROLEPLAY_SCENARIOS
    assert all(s.tier in SCENARIO_TIERS for s in ROLEPLAY_SCENARIOS)


def test_slugs_unique() -> None:
    slugs = [s.slug for s in ROLEPLAY_SCENARIOS]
    assert len(slugs) == len(set(slugs))
