import { useState } from "react";
import { apiClient } from "../api/client";
import type { SessionReplay } from "../api/types";

export type ReplayPhase = "idle" | "loading" | "ready" | "none" | "error";

// E3: opt-in (nothing is fetched until load()), same shape as useDictation. "none"
// = the server has no recording (recording is off by default, or it was pruned).
export function useSessionReplay() {
  const [phase, setPhase] = useState<ReplayPhase>("idle");
  const [replay, setReplay] = useState<SessionReplay | null>(null);

  async function load() {
    setPhase("loading");
    try {
      const result = await apiClient.getLatestReplay();
      setReplay(result);
      setPhase(result ? "ready" : "none");
    } catch {
      setPhase("error");
    }
  }

  return { phase, replay, load };
}
