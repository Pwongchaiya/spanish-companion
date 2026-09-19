import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: {
    listMistakeSummary: vi.fn(),
    listTopicCoverage: vi.fn(),
    getSpeakingTotal: vi.fn(),
    getUnflaggedStreak: vi.fn(),
  },
}));

import { useProgress } from "./useProgress";
import { apiClient } from "../api/client";

describe("useProgress", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.getSpeakingTotal as any).mockResolvedValue({ total_seconds: 0, session_count: 0 });
    (apiClient.getUnflaggedStreak as any).mockResolvedValue({ longest: 0, current: 0 });
  });

  it("loads mistakes and topics independently on mount", async () => {
    (apiClient.listMistakeSummary as any).mockResolvedValue([
      { id: 1, profile_id: 1, category: "ser_estar", occurrence_count: 2, last_seen_at: "2026-01-01T00:00:00", status: "active" },
    ]);
    (apiClient.listTopicCoverage as any).mockResolvedValue([
      { topic: "ser-vs-estar", covered: true, first_covered_at: "2026-01-01T00:00:00" },
    ]);

    const { result } = renderHook(() => useProgress());

    await waitFor(() => expect(result.current.hasLoaded).toBe(true));

    expect(result.current.mistakes).toHaveLength(1);
    expect(result.current.topics).toHaveLength(1);
  });

  it("keeps hasLoaded false when only the mistakes fetch has resolved", async () => {
    (apiClient.listMistakeSummary as any).mockResolvedValue([]);
    (apiClient.listTopicCoverage as any).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useProgress());

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.hasLoaded).toBe(false);
  });

  it("loads the speaking total and streak alongside mistakes and topics", async () => {
    (apiClient.listMistakeSummary as any).mockResolvedValue([]);
    (apiClient.listTopicCoverage as any).mockResolvedValue([]);
    (apiClient.getSpeakingTotal as any).mockResolvedValue({ total_seconds: 1800, session_count: 1 });
    (apiClient.getUnflaggedStreak as any).mockResolvedValue({ longest: 3, current: 1 });

    const { result } = renderHook(() => useProgress());

    await waitFor(() => expect(result.current.speaking).not.toBeNull());
    await waitFor(() => expect(result.current.streak).not.toBeNull());

    expect(result.current.speaking).toEqual({ total_seconds: 1800, session_count: 1 });
    expect(result.current.streak).toEqual({ longest: 3, current: 1 });
  });

  it("does not gate hasLoaded on the session_log reads", async () => {
    // A slow /progress/speaking must not hold back the mistakes/topics
    // empty-state copy -- that is what hasLoaded exists for.
    (apiClient.listMistakeSummary as any).mockResolvedValue([]);
    (apiClient.listTopicCoverage as any).mockResolvedValue([]);
    (apiClient.getSpeakingTotal as any).mockReturnValue(new Promise(() => {}));
    (apiClient.getUnflaggedStreak as any).mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useProgress());

    await waitFor(() => expect(result.current.hasLoaded).toBe(true));
    expect(result.current.speaking).toBeNull();
  });
});
