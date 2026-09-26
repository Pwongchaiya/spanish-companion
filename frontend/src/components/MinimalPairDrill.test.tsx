import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: {
    synthesizeSpeech: vi.fn(),
  },
}));

vi.mock("../data/minimalPairs", async () => {
  const actual = await vi.importActual<typeof import("../data/minimalPairs")>("../data/minimalPairs");
  return {
    ...actual,
    // Deterministic pair/word for every test -- the real random pickers
    // are covered by their own unit tests below.
    pickRandomPair: vi.fn(() => ({ a: "pero", b: "perro" })),
    pickRandomWord: vi.fn(() => "perro"),
  };
});

import { MinimalPairDrill } from "./MinimalPairDrill";
import { apiClient } from "../api/client";
import type * as MinimalPairsModule from "../data/minimalPairs";

describe("MinimalPairDrill", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.synthesizeSpeech as any).mockResolvedValue(new Blob(["audio"], { type: "audio/wav" }));
    globalThis.URL.createObjectURL = vi.fn(() => "blob:mock-url");
  });

  it("renders both words of the picked pair as options", () => {
    render(<MinimalPairDrill />);
    expect(screen.getByRole("button", { name: "pero" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "perro" })).toBeTruthy();
  });

  it("calls synthesizeSpeech with the played word when Play is clicked", async () => {
    render(<MinimalPairDrill />);
    fireEvent.click(screen.getByRole("button", { name: /play/i }));

    await waitFor(() => expect(apiClient.synthesizeSpeech).toHaveBeenCalledWith("perro"));
  });

  it("marks the choice correct when the picked word matches the played word", () => {
    render(<MinimalPairDrill />);
    fireEvent.click(screen.getByRole("button", { name: "perro" }));

    expect(screen.getByText(/Correct — that was perro/)).toBeTruthy();
  });

  it("marks the choice incorrect when the picked word does not match the played word", () => {
    render(<MinimalPairDrill />);
    fireEvent.click(screen.getByRole("button", { name: "pero" }));

    expect(screen.getByText(/Not quite — that was perro/)).toBeTruthy();
  });

  it("ignores further picks once a result has been chosen", () => {
    render(<MinimalPairDrill />);
    fireEvent.click(screen.getByRole("button", { name: "pero" }));
    expect(screen.getByText(/Not quite/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "perro" }));
    // Still shows the original (incorrect) result, not overwritten.
    expect(screen.getByText(/Not quite/)).toBeTruthy();
  });

  it("shows a Next pair control only after a choice has been made", () => {
    render(<MinimalPairDrill />);
    expect(screen.queryByRole("button", { name: "Next pair" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "pero" }));
    expect(screen.getByRole("button", { name: "Next pair" })).toBeTruthy();
  });
});

describe("minimalPairs data helpers (real implementation, not the mock above)", () => {
  async function loadReal() {
    return vi.importActual<typeof MinimalPairsModule>("../data/minimalPairs");
  }

  it("pickRandomPair always returns one of the known pairs", async () => {
    const { MINIMAL_PAIRS, pickRandomPair } = await loadReal();
    for (let i = 0; i < 20; i++) {
      const pair = pickRandomPair(MINIMAL_PAIRS);
      expect(MINIMAL_PAIRS).toContainEqual(pair);
    }
  });

  it("pickRandomWord always returns one of the pair's two words", async () => {
    const { pickRandomWord } = await loadReal();
    const pair = { a: "pero", b: "perro" };
    for (let i = 0; i < 20; i++) {
      const word = pickRandomWord(pair);
      expect([pair.a, pair.b]).toContain(word);
    }
  });
});
