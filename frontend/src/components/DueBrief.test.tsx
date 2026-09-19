import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { DueBrief } from "./DueBrief";

describe("DueBrief", () => {
  it("renders nothing when undefined or empty", () => {
    expect(render(<DueBrief />).container.firstChild).toBeNull();
    expect(render(<DueBrief due={[]} />).container.firstChild).toBeNull();
  });

  it("renders a chip per due pattern", () => {
    render(
      <DueBrief
        due={[
          { category: "past_tense", occurrence_count: 3, days_overdue: 2 },
          { category: "gender", occurrence_count: 1, days_overdue: 0 },
        ]}
      />,
    );
    expect(screen.getByText("Due for review")).toBeTruthy();
    expect(screen.getByText("past tense")).toBeTruthy();
    expect(screen.getByText("gender")).toBeTruthy();
  });
});
