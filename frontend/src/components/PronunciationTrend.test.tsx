import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PronunciationTrend } from "./PronunciationTrend";

const point = (accuracy: number, fluency: number) => ({
  created_at: "2026-01-01T00:00:00",
  accuracy,
  fluency,
  overall: 0,
});

describe("PronunciationTrend", () => {
  it("shows the empty state once loaded with no attempts", () => {
    render(<PronunciationTrend trend={[]} hasLoaded={true} />);
    expect(screen.getByText("No shadowing attempts yet")).toBeTruthy();
  });

  it("does not claim emptiness before the fetch resolves", () => {
    render(<PronunciationTrend trend={[]} hasLoaded={false} />);
    expect(screen.queryByText("No shadowing attempts yet")).toBeNull();
  });

  it("labels first and last values for accuracy and fluency", () => {
    render(<PronunciationTrend trend={[point(60, 50), point(70, 55), point(85, 72)]} hasLoaded={true} />);
    expect(screen.getByText("60 → 85")).toBeTruthy();
    expect(screen.getByText("50 → 72")).toBeTruthy();
    expect(screen.getByRole("img", { name: "Accuracy from 60 to 85" })).toBeTruthy();
  });

  it("draws a line for several points and none for a single point", () => {
    const { container, rerender } = render(<PronunciationTrend trend={[point(60, 50), point(80, 70)]} hasLoaded={true} />);
    expect(container.querySelectorAll("polyline")).toHaveLength(2);
    rerender(<PronunciationTrend trend={[point(60, 50)]} hasLoaded={true} />);
    expect(container.querySelectorAll("polyline")).toHaveLength(0);
    expect(container.querySelectorAll("circle")).toHaveLength(2);
  });
});
