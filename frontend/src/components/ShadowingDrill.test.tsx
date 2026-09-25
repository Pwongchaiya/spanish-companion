import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: { synthesizeSpeech: vi.fn(), assessPronunciation: vi.fn() },
}));
vi.mock("../audio/encodeWav", () => ({ blobToWav16k: vi.fn() }));
vi.mock("../hooks/useRecorder", () => ({ useRecorder: vi.fn(), MAX_RECORD_MS: 15_000 }));
vi.mock("../data/shadowingSentences", () => ({
  pickRandomSentence: vi.fn(() => ({ es: "El perro corre.", en: "The dog runs." })),
}));

import { ShadowingDrill } from "./ShadowingDrill";
import { apiClient } from "../api/client";
import { blobToWav16k } from "../audio/encodeWav";
import { useRecorder } from "../hooks/useRecorder";
import { pickRandomSentence } from "../data/shadowingSentences";
import type { PronunciationResult } from "../api/types";

const result: PronunciationResult = {
  reference_text: "El perro corre.",
  accuracy: 88,
  fluency: 77,
  completeness: 100,
  prosody: null,
  overall: 84,
  words: [{ word: "perro", accuracy: 90, error_type: "None", phonemes: [] }],
  created_at: "2026-01-01T00:00:00",
};

function mockRecorder(overrides: Partial<ReturnType<typeof useRecorder>> = {}) {
  vi.mocked(useRecorder).mockReturnValue({
    status: "idle",
    blob: null,
    error: null,
    start: vi.fn(),
    stop: vi.fn(),
    ...overrides,
  });
}

describe("ShadowingDrill", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    URL.createObjectURL = vi.fn(() => "blob:ref");
    mockRecorder();
  });

  it("plays the reference via synthesizeSpeech", async () => {
    vi.mocked(apiClient.synthesizeSpeech).mockResolvedValue(new Blob());
    render(<ShadowingDrill />);
    fireEvent.click(screen.getByRole("button", { name: /play/i }));

    await waitFor(() => expect(apiClient.synthesizeSpeech).toHaveBeenCalledWith("El perro corre."));
    expect(await screen.findByTestId("shadow-audio")).toBeTruthy();
  });

  it("wires Record to the recorder", () => {
    const start = vi.fn();
    mockRecorder({ start });
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: /record/i }));
    expect(start).toHaveBeenCalledTimes(1);
    expect(screen.getByText("The dog runs.")).toBeTruthy();
  });

  it("shows Stop & score while recording", () => {
    const stop = vi.fn();
    mockRecorder({ status: "recording", stop });
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: /stop/i }));
    expect(stop).toHaveBeenCalledTimes(1);
  });

  it("encodes then assesses a finished take and shows scores, dropping prosody", async () => {
    const take = new Blob(["x"]);
    const wav = new Blob(["wav"]);
    mockRecorder({ status: "done", blob: take });
    vi.mocked(blobToWav16k).mockResolvedValue(wav);
    vi.mocked(apiClient.assessPronunciation).mockResolvedValue({ ...result, prosody: 71 });
    render(<ShadowingDrill />);

    await waitFor(() => expect(apiClient.assessPronunciation).toHaveBeenCalledWith(wav, "El perro corre.", false));
    expect(blobToWav16k).toHaveBeenCalledWith(take);
    expect(await screen.findByText("84")).toBeTruthy();
    expect(screen.getByText("88")).toBeTruthy();
    expect(screen.getByText("77")).toBeTruthy();
    expect(screen.getByText("100")).toBeTruthy();
    expect(screen.queryByText("Prosody")).toBeNull();
    expect(screen.queryByText("71")).toBeNull();
    expect(screen.getByRole("button", { name: /perro/ })).toBeTruthy();
  });

  it("surfaces the server error message on failure and keeps Try again", async () => {
    mockRecorder({ status: "done", blob: new Blob(["x"]) });
    vi.mocked(blobToWav16k).mockResolvedValue(new Blob());
    vi.mocked(apiClient.assessPronunciation).mockRejectedValue(new Error("Audio too large"));
    render(<ShadowingDrill />);

    expect(await screen.findByText("Audio too large")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });

  it("shows the recorder error (mic denied)", () => {
    mockRecorder({ status: "error", error: "Microphone permission denied." });
    render(<ShadowingDrill />);

    expect(screen.getByText("Microphone permission denied.")).toBeTruthy();
  });

  it("Next sentence picks a new sentence excluding the current one and clears the result", async () => {
    mockRecorder({ status: "done", blob: new Blob(["x"]) });
    vi.mocked(blobToWav16k).mockResolvedValue(new Blob());
    vi.mocked(apiClient.assessPronunciation).mockResolvedValue(result);
    vi.mocked(pickRandomSentence)
      .mockReturnValueOnce({ es: "El perro corre.", en: "The dog runs." })
      .mockReturnValueOnce({ es: "Otra frase.", en: "Another sentence." });
    render(<ShadowingDrill />);
    await screen.findByText("84");

    fireEvent.click(screen.getAllByRole("button", { name: /next sentence/i })[0]);

    expect(pickRandomSentence).toHaveBeenLastCalledWith("El perro corre.");
    expect(screen.getByText("Otra frase.")).toBeTruthy();
    expect(screen.getByText("Another sentence.")).toBeTruthy();
    expect(screen.queryByText("84")).toBeNull();
  });

  describe("single-word drill", () => {
    const weakResult: PronunciationResult = {
      ...result,
      words: [{ word: "perro", accuracy: 50, error_type: "Mispronunciation", phonemes: [] }],
    };

    async function openDrill() {
      const take = new Blob(["take"]);
      const start = vi.fn();
      mockRecorder({ status: "done", blob: take, start });
      vi.mocked(blobToWav16k).mockResolvedValue(new Blob(["wav"]));
      vi.mocked(apiClient.assessPronunciation).mockResolvedValueOnce(weakResult);
      const view = render(<ShadowingDrill />);
      await screen.findByText("Fix", { exact: false });
      fireEvent.click(screen.getByRole("button", { name: "● Record just this word" }));
      expect(start).toHaveBeenCalledTimes(1);
      return { ...view, start, take };
    }

    function finishDrill(view: { rerender: (ui: React.ReactElement) => void }, take: Blob) {
      mockRecorder({ status: "done", blob: new Blob(["drill"]) });
      void take;
      view.rerender(<ShadowingDrill />);
    }

    it("0.6x button synthesizes the word at rate 0.6", async () => {
      mockRecorder({ status: "done", blob: new Blob(["x"]) });
      vi.mocked(blobToWav16k).mockResolvedValue(new Blob());
      vi.mocked(apiClient.assessPronunciation).mockResolvedValue(weakResult);
      vi.mocked(apiClient.synthesizeSpeech).mockResolvedValue(new Blob());
      render(<ShadowingDrill />);

      fireEvent.click(await screen.findByRole("button", { name: "◐ 0.6×" }));

      await waitFor(() => expect(apiClient.synthesizeSpeech).toHaveBeenCalledWith("perro", 0.6));
    });

    it.each([
      [85, "improved", "85 / 100"],
      [41, "weak", "41 / 100"],
    ])("scores the word via is_word_drill and reads words[0].accuracy (%i -> %s)", async (accuracy, _phase, text) => {
      const { take, ...view } = await openDrill();
      const drillWav = new Blob(["drillwav"]);
      vi.mocked(blobToWav16k).mockResolvedValue(drillWav);
      // overall is deliberately the opposite band: it must be ignored.
      vi.mocked(apiClient.assessPronunciation).mockResolvedValueOnce({
        ...result,
        overall: accuracy >= 80 ? 10 : 99,
        words: [{ word: "perro", accuracy, error_type: "None", phonemes: [] }],
      });

      finishDrill(view, take);

      expect(await screen.findByText(text, { exact: false })).toBeTruthy();
      expect(apiClient.assessPronunciation).toHaveBeenLastCalledWith(drillWav, "perro", true);
      expect(screen.queryByRole("button", { name: /↺ Whole sentence/ }) !== null).toBe(accuracy >= 80);
    });

    it("renders state 10 with the raw detail when the drill call is rejected", async () => {
      const { take, ...view } = await openDrill();
      vi.mocked(apiClient.assessPronunciation).mockRejectedValueOnce(new Error("Azure found no speech"));

      finishDrill(view, take);

      expect(await screen.findByText("Azure found no speech")).toBeTruthy();
      expect(screen.getByRole("status").textContent).toMatch(/Record the word again/);
    });
  });
});
