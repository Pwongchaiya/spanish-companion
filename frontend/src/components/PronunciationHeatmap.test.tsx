import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { PronunciationHeatmap, band } from "./PronunciationHeatmap";
import type { WordScore } from "../api/types";

const WORDS: WordScore[] = [
  {
    word: "perro",
    accuracy: 92,
    error_type: "None",
    phonemes: [
      { phoneme: "r", accuracy: 95 },
      { phoneme: "o", accuracy: 70 },
    ],
  },
  { word: "rápido", accuracy: 65, error_type: "None", phonemes: [] },
  { word: "corre", accuracy: 40, error_type: "Mispronunciation", phonemes: [{ phoneme: "rr", accuracy: 30 }] },
  { word: "el", accuracy: null, error_type: "Omission", phonemes: [] },
];

describe("band", () => {
  it("splits at 80 and 60, null is none", () => {
    expect([band(80), band(79), band(60), band(59), band(null)]).toEqual(["good", "warn", "warn", "poor", "none"]);
  });
});

describe("PronunciationHeatmap", () => {
  it("applies band classes and shows numeric scores as text", () => {
    render(<PronunciationHeatmap words={WORDS} />);
    const perro = screen.getByRole("button", { name: "perro, 92" });
    expect(perro.className).toContain("good");
    expect(perro.textContent).toContain("92");
    expect(screen.getByRole("button", { name: "rápido, 65" }).className).toContain("warn");
    expect(screen.getByRole("button", { name: /corre, 40/ }).className).toContain("poor");
  });

  it("marks error words distinctly with the error type visible", () => {
    render(<PronunciationHeatmap words={WORDS} />);
    const corre = screen.getByRole("button", { name: "corre, 40, Mispronunciation" });
    expect(corre.className).toContain("has-error");
    expect(corre.textContent).toContain("Mispronunciation");
    expect(screen.getByRole("button", { name: "perro, 92" }).className).not.toContain("has-error");
  });

  it("handles null accuracy", () => {
    render(<PronunciationHeatmap words={WORDS} />);
    const el = screen.getByRole("button", { name: "el, no score, Omission" });
    expect(el.className).toContain("none");
  });

  it("clicking a word reveals phoneme chips with accuracy; click again collapses", () => {
    render(<PronunciationHeatmap words={WORDS} />);
    fireEvent.click(screen.getByRole("button", { name: "perro, 92" }));
    const list = screen.getByRole("list", { name: "Phonemes for perro" });
    expect(list.textContent).toContain("r");
    expect(list.textContent).toContain("95");
    expect(list.textContent).toContain("70");
    fireEvent.click(screen.getByRole("button", { name: "perro, 92" }));
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("shows a fallback for a word with empty phonemes", () => {
    render(<PronunciationHeatmap words={WORDS} />);
    fireEvent.click(screen.getByRole("button", { name: "rápido, 65" }));
    expect(screen.getByText("No phoneme detail")).toBeTruthy();
  });

  it("renders no buttons for empty words", () => {
    render(<PronunciationHeatmap words={[]} />);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
  });
});
