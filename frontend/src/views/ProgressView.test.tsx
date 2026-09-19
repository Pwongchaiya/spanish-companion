import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProgressView, formatSpoken, nextMilestone } from "./ProgressView";
import { useProgress } from "../hooks/useProgress";

vi.mock("../hooks/useProgress");

const mockUseProgress = vi.mocked(useProgress);

function mockProgress(overrides: Partial<ReturnType<typeof useProgress>>) {
  mockUseProgress.mockReturnValue({
    mistakes: [],
    topics: [],
    speaking: null,
    streak: null,
    hasLoaded: true,
    ...overrides,
  });
}

describe("ProgressView", () => {
  it("shows only active patterns, sorted by occurrence count descending", () => {
    mockProgress({
      mistakes: [
        { id: 1, profile_id: 1, category: "gender", occurrence_count: 2, last_seen_at: "2026-01-01T00:00:00", status: "active" },
        { id: 2, profile_id: 1, category: "ser_estar", occurrence_count: 5, last_seen_at: "2026-01-02T00:00:00", status: "active" },
        { id: 3, profile_id: 1, category: "subjunctive", occurrence_count: 9, last_seen_at: "2026-01-03T00:00:00", status: "resolved" },
      ],
    });

    render(<ProgressView />);

    const rows = screen.getAllByText(/^(gender|ser_estar|subjunctive)$/);
    expect(rows.map((r) => r.textContent)).toEqual(["ser_estar", "gender"]);
  });

  it("shows the empty-state message once loaded with no recurring mistakes", () => {
    mockProgress({ mistakes: [], hasLoaded: true });

    render(<ProgressView />);

    expect(screen.getByText(/nothing recurring yet/i)).toBeTruthy();
  });

  it("renders a covered-count summary and marks each topic covered or not", () => {
    mockProgress({
      topics: [
        { topic: "ser-vs-estar", covered: true, first_covered_at: "2026-01-01T00:00:00" },
        { topic: "subjunctive-basics", covered: false, first_covered_at: null },
      ],
    });

    render(<ProgressView />);

    expect(screen.getByText("1 / 2 topics covered")).toBeTruthy();
    expect(screen.getByText("ser-vs-estar")).toBeTruthy();
    expect(screen.getByText("subjunctive-basics")).toBeTruthy();
    expect(screen.getByText(/since/)).toBeTruthy();
  });
});

describe("formatSpoken", () => {
  it("shows minutes below an hour and one decimal hour above it", () => {
    expect(formatSpoken(0)).toBe("0 min");
    expect(formatSpoken(90 * 60)).toBe("1.5 h");
    expect(formatSpoken(59 * 60)).toBe("59 min");
    // Exactly one hour is the boundary -- must read as hours, not "60 min".
    expect(formatSpoken(3600)).toBe("1.0 h");
  });
});

describe("nextMilestone", () => {
  it("returns the first milestone above the current total", () => {
    expect(nextMilestone(0)).toBe(1);
    expect(nextMilestone(2 * 3600)).toBe(5);
    // On a milestone exactly -> the next one up, not the one just hit.
    expect(nextMilestone(5 * 3600)).toBe(10);
  });

  it("returns null once past the last milestone", () => {
    expect(nextMilestone(150 * 3600)).toBeNull();
  });
});

describe("ProgressView meters", () => {
  it("renders the speaking total, session count and next milestone", () => {
    mockProgress({ speaking: { total_seconds: 2 * 3600, session_count: 3 } });

    render(<ProgressView />);

    expect(screen.getByText("2.0 h")).toBeTruthy();
    expect(screen.getByText(/3 sessions/)).toBeTruthy();
    expect(screen.getByText(/next 5 h/)).toBeTruthy();
  });

  it("singularises a lone session and drops the milestone once past the ladder", () => {
    mockProgress({ speaking: { total_seconds: 150 * 3600, session_count: 1 } });

    render(<ProgressView />);

    // Exact text, not a substring: "1 sessions" would satisfy /1 session/.
    expect(screen.getByText("1 session")).toBeTruthy();
    expect(screen.queryByText(/next/)).toBeNull();
  });

  it("renders current and best streak", () => {
    mockProgress({ streak: { longest: 4, current: 2 } });

    render(<ProgressView />);

    expect(screen.getByText("2")).toBeTruthy();
    expect(screen.getByText(/best 4/)).toBeTruthy();
  });

  it("shows a placeholder for each meter before its fetch resolves", () => {
    mockProgress({ speaking: null, streak: null });

    render(<ProgressView />);

    expect(screen.getAllByText("—")).toHaveLength(2);
  });
});
