import { describe, it, expect } from "vitest";
import { formatOffset, markerPercent, seekTarget } from "./replayTimeline";

describe("replayTimeline", () => {
  it("places a marker proportionally and clamps to the track", () => {
    expect(markerPercent(30, 120)).toBe(25);
    expect(markerPercent(-5, 120)).toBe(0);
    expect(markerPercent(500, 120)).toBe(100);
  });

  it("does not divide by a zero or missing duration", () => {
    expect(markerPercent(10, 0)).toBe(0);
    expect(markerPercent(10, Number.NaN)).toBe(0);
  });

  it("seeks a lead-in before the flag, never before 0 or past the end", () => {
    expect(seekTarget(30, 120)).toBe(28);
    expect(seekTarget(1, 120)).toBe(0);
    expect(seekTarget(500, 120)).toBe(120);
  });

  it("formats offsets as m:ss", () => {
    expect(formatOffset(0)).toBe("0:00");
    expect(formatOffset(65.9)).toBe("1:05");
    expect(formatOffset(600)).toBe("10:00");
  });
});
