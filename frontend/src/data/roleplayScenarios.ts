// Static roleplay scenario list (LearnerProfile Phase 4). Kept in sync by
// hand with the backend's copy (api/data/roleplay_scenarios.py) -- same
// duplicate-rather-than-fetch reasoning as minimalPairs.ts: static data the
// client needs at render time, manual-pick-only (no auto-suggestion), so a
// round trip buys nothing.
export interface RoleplayScenario {
  slug: string;
  label: string;
  setting: string;
}

export const ROLEPLAY_SCENARIOS: RoleplayScenario[] = [
  {
    slug: "ordering_coffee",
    label: "Ordering coffee",
    setting: "You are a barista at a small café. The user is a customer ordering a drink and something to eat.",
  },
  {
    slug: "job_interview",
    label: "Job interview",
    setting: "You are an interviewer at a company. The user is a candidate interviewing for a job.",
  },
  {
    slug: "casual_chat",
    label: "Casual chat",
    setting: "You are a friend catching up with the user about their week, no particular topic.",
  },
];
