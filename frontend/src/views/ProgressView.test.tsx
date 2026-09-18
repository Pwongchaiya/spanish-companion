import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ProgressView } from "./ProgressView";
import { useProgress } from "../hooks/useProgress";

vi.mock("../hooks/useProgress");

const mockUseProgress = vi.mocked(useProgress);

function mockProgress(overrides: Partial<ReturnType<typeof useProgress>>) {
  mockUseProgress.mockReturnValue({
    mistakes: [],
    topics: [],
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
