import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: {
    getDictationExercise: vi.fn(),
    checkDictation: vi.fn(),
    synthesizeSpeech: vi.fn(),
  },
}));

import { DictationPanel } from "./DictationPanel";
import { apiClient } from "../api/client";

const api = apiClient as unknown as Record<string, ReturnType<typeof vi.fn>>;

async function startExercise() {
  api.getDictationExercise.mockResolvedValue({ flag_id: "f1", target: "él está" });
  render(<DictationPanel />);
  fireEvent.click(screen.getByRole("button", { name: /dictation/i }));
  await screen.findByLabelText(/type the sentence/i);
}

describe("DictationPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
  });

  it("fetches nothing until the learner opts in", () => {
    render(<DictationPanel />);
    expect(api.getDictationExercise).not.toHaveBeenCalled();
  });

  it("shows a friendly message on 404 (no flags)", async () => {
    api.getDictationExercise.mockRejectedValue(Object.assign(new Error("none"), { status: 404 }));
    render(<DictationPanel />);
    fireEvent.click(screen.getByRole("button", { name: /dictation/i }));
    await screen.findByText(/no other flagged sentence/i);
    expect(api.getDictationExercise).toHaveBeenCalledTimes(1);
  });

  it("plays the target via TTS on Listen", async () => {
    await startExercise();
    api.synthesizeSpeech.mockResolvedValue(new Blob(["a"], { type: "audio/wav" }));
    fireEvent.click(screen.getByRole("button", { name: /listen/i }));
    await screen.findByTestId("dictation-audio");
    expect(api.synthesizeSpeech).toHaveBeenCalledWith("él está");
    expect(api.synthesizeSpeech).toHaveBeenCalledTimes(1);
  });

  it("submits typed text and renders per-word accent differences", async () => {
    await startExercise();
    api.checkDictation.mockResolvedValue({
      flag_id: "f1",
      target: "él está",
      typed_text: "el está",
      matches: false,
      words: [
        { target: "él", typed: "el", status: "accent" },
        { target: "está", typed: "está", status: "ok" },
      ],
    });
    fireEvent.change(screen.getByLabelText(/type the sentence/i), { target: { value: "el está" } });
    fireEvent.click(screen.getByRole("button", { name: "Check" }));
    const result = await screen.findByTestId("dictation-result");
    expect(api.checkDictation).toHaveBeenCalledWith("f1", "el está");
    expect(result.textContent).toContain("Not quite");
    expect(result.querySelector('[data-status="accent"]')?.textContent).toContain("él");
  });

  it("reports an exact match", async () => {
    await startExercise();
    api.checkDictation.mockResolvedValue({
      flag_id: "f1",
      target: "él está",
      typed_text: "él está",
      matches: true,
      words: [
        { target: "él", typed: "él", status: "ok" },
        { target: "está", typed: "está", status: "ok" },
      ],
    });
    fireEvent.change(screen.getByLabelText(/type the sentence/i), { target: { value: "él está" } });
    fireEvent.click(screen.getByRole("button", { name: "Check" }));
    await waitFor(() => expect(screen.getByText("Exact match.")).toBeTruthy());
  });

  it("asks for another sentence excluding the current one", async () => {
    await startExercise();
    api.checkDictation.mockResolvedValue({ flag_id: "f1", target: "x", typed_text: "x", matches: true, words: [] });
    fireEvent.change(screen.getByLabelText(/type the sentence/i), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: "Check" }));
    await screen.findByTestId("dictation-result");
    fireEvent.click(screen.getByRole("button", { name: "Another" }));
    await waitFor(() => expect(api.getDictationExercise).toHaveBeenCalledTimes(2));
    expect(api.getDictationExercise).toHaveBeenLastCalledWith("f1");
  });
});
