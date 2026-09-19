import { describe, expect, it } from "vitest";
import { ROLEPLAY_SCENARIOS, TIER_ORDER, groupScenariosByTier } from "./roleplayScenarios";

describe("roleplayScenarios", () => {
  it("every scenario has a valid tier", () => {
    expect(ROLEPLAY_SCENARIOS.every((s) => TIER_ORDER.includes(s.tier))).toBe(true);
  });

  it("groups by tier in beginner-to-advanced order, dropping empty tiers", () => {
    const groups = groupScenariosByTier(ROLEPLAY_SCENARIOS.filter((s) => s.tier !== "intermediate"));
    expect(groups.map((g) => g.tier)).toEqual(["beginner", "advanced"]);
    expect(groupScenariosByTier().flatMap((g) => g.scenarios)).toHaveLength(ROLEPLAY_SCENARIOS.length);
  });
});
