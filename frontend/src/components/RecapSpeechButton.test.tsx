import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({ apiClient: { getRecapSpeech: vi.fn() } }));

import { RecapSpeechButton } from "./RecapSpeechButton";
import { apiClient } from "../api/client";

describe("RecapSpeechButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    globalThis.URL.createObjectURL = vi.fn(() => "blob:mock-url");
  });

  it("fetches the recap audio once and plays it on click", async () => {
    (apiClient.getRecapSpeech as any).mockResolvedValue(new Blob(["a"], { type: "audio/wav" }));
    render(<RecapSpeechButton />);
    expect(screen.queryByTestId("recap-audio")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /listen/i }));

    await waitFor(() => expect(screen.getByTestId("recap-audio").getAttribute("src")).toBe("blob:mock-url"));
    expect(apiClient.getRecapSpeech).toHaveBeenCalledTimes(1);
  });

  it("says there is nothing to read when the backend returns no audio", async () => {
    (apiClient.getRecapSpeech as any).mockResolvedValue(null);
    render(<RecapSpeechButton />);
    fireEvent.click(screen.getByRole("button", { name: /listen/i }));

    await waitFor(() => expect(screen.getByText(/No recap to read yet/)).toBeTruthy());
    expect(screen.queryByTestId("recap-audio")).toBeNull();
  });

  it("shows an error when the request fails", async () => {
    (apiClient.getRecapSpeech as any).mockRejectedValue(new Error("boom"));
    render(<RecapSpeechButton />);
    fireEvent.click(screen.getByRole("button", { name: /listen/i }));

    await waitFor(() => expect(screen.getByText(/Couldn't load the audio/)).toBeTruthy());
  });
});
