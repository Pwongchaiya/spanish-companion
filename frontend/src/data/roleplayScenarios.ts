// Static roleplay scenario list (LearnerProfile Phase 4). Kept in sync by
// hand with the backend's copy (api/data/roleplay_scenarios.py) -- same
// duplicate-rather-than-fetch reasoning as minimalPairs.ts: static data the
// client needs at render time, manual-pick-only (no auto-suggestion), so a
// round trip buys nothing.
export type ScenarioTier = "beginner" | "intermediate" | "advanced";

export interface RoleplayScenario {
  slug: string;
  label: string;
  setting: string;
  tier: ScenarioTier;
}

export const TIER_ORDER: ScenarioTier[] = ["beginner", "intermediate", "advanced"];

export const TIER_LABELS: Record<ScenarioTier, string> = {
  beginner: "Beginner (A1-A2)",
  intermediate: "Intermediate (B1-B2)",
  advanced: "Advanced (C1+)",
};

export const ROLEPLAY_SCENARIOS: RoleplayScenario[] = [
  {
    slug: "ordering_coffee",
    label: "Ordering coffee",
    setting: "You are a barista at a small café. The user is a customer ordering a drink and something to eat.",
    tier: "beginner",
  },
  {
    slug: "job_interview",
    label: "Job interview",
    setting: "You are an interviewer at a company. The user is a candidate interviewing for a job.",
    tier: "advanced",
  },
  {
    slug: "casual_chat",
    label: "Casual chat",
    setting: "You are a friend catching up with the user about their week, no particular topic.",
    tier: "intermediate",
  },
];

// Non-empty tiers only, in beginner -> advanced order, for <optgroup> rendering.
export function groupScenariosByTier(
  scenarios: RoleplayScenario[] = ROLEPLAY_SCENARIOS,
): { tier: ScenarioTier; label: string; scenarios: RoleplayScenario[] }[] {
  return TIER_ORDER.map((tier) => ({
    tier,
    label: TIER_LABELS[tier],
    scenarios: scenarios.filter((s) => s.tier === tier),
  })).filter((g) => g.scenarios.length > 0);
}
