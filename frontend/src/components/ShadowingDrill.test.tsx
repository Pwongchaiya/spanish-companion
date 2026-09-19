import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: { synthesizeSpeech: vi.fn(), assessPronunciation: vi.fn() },
}));
vi.mock("../audio/encodeWav", () => ({ blobToWav16k: vi.fn() }));
vi.mock("../hooks/useRecorder", () => ({ useRecorder: vi.fn() }));
vi.mock("../data/shadowingSentences", () => ({
  pickRandomSentence: vi.fn(() => "El perro corre."),
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

  it("wires Record to the recorder and disables Submit until a take exists", () => {
    const start = vi.fn();
    mockRecorder({ start });
    render(<ShadowingDrill />);

    expect((screen.getByRole("button", { name: "Submit" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /record/i }));
    expect(start).toHaveBeenCalledTimes(1);
  });

  it("shows Stop while recording", () => {
    const stop = vi.fn();
    mockRecorder({ status: "recording", stop });
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: /stop/i }));
    expect(stop).toHaveBeenCalledTimes(1);
  });

  it("encodes then assesses on Submit and shows scores, hiding null prosody", async () => {
    const take = new Blob(["x"]);
    const wav = new Blob(["wav"]);
    mockRecorder({ status: "done", blob: take });
    vi.mocked(blobToWav16k).mockResolvedValue(wav);
    vi.mocked(apiClient.assessPronunciation).mockResolvedValue(result);
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => expect(apiClient.assessPronunciation).toHaveBeenCalledWith(wav, "El perro corre."));
    expect(blobToWav16k).toHaveBeenCalledWith(take);
    expect(await screen.findByText("84")).toBeTruthy();
    expect(screen.getByText("88")).toBeTruthy();
    expect(screen.getByText("77")).toBeTruthy();
    expect(screen.getByText("100")).toBeTruthy();
    expect(screen.queryByText("Prosody")).toBeNull();
    expect(screen.getByRole("button", { name: /perro/ })).toBeTruthy();
  });

  it("shows prosody when present", async () => {
    mockRecorder({ status: "done", blob: new Blob(["x"]) });
    vi.mocked(blobToWav16k).mockResolvedValue(new Blob());
    vi.mocked(apiClient.assessPronunciation).mockResolvedValue({ ...result, prosody: 71 });
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("Prosody")).toBeTruthy();
    expect(screen.getByText("71")).toBeTruthy();
  });

  it("surfaces the server error message on failure", async () => {
    mockRecorder({ status: "done", blob: new Blob(["x"]) });
    vi.mocked(blobToWav16k).mockResolvedValue(new Blob());
    vi.mocked(apiClient.assessPronunciation).mockRejectedValue(new Error("Audio too large"));
    render(<ShadowingDrill />);

    fireEvent.click(screen.getByRole("button", { name: "Submit" }));

    expect(await screen.findByText("Audio too large")).toBeTruthy();
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
    vi.mocked(pickRandomSentence).mockReturnValueOnce("El perro corre.").mockReturnValueOnce("Otra frase.");
    render(<ShadowingDrill />);
    fireEvent.click(screen.getByRole("button", { name: "Submit" }));
    await screen.findByText("84");

    fireEvent.click(screen.getByRole("button", { name: "Next sentence" }));

    expect(pickRandomSentence).toHaveBeenLastCalledWith("El perro corre.");
    expect(screen.getByText("Otra frase.")).toBeTruthy();
    expect(screen.queryByText("84")).toBeNull();
  });
});
