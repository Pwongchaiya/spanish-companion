import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: {
    getLatestReplay: vi.fn(),
  },
}));

import { ReplayPanel } from "./ReplayPanel";
import { apiClient } from "../api/client";

const api = apiClient as unknown as Record<string, ReturnType<typeof vi.fn>>;

const REPLAY = {
  session_log_id: 4,
  duration_seconds: 100,
  audio_url: "/review/sessions/4/audio",
  flags: [
    {
      flag_id: "f1",
      offset_seconds: 30,
      said: "yo tiene",
      corrected: "yo tengo",
      category: "conjugation",
      status: "mastered",
    },
  ],
};

describe("ReplayPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  });

  it("fetches nothing until the learner opts in", () => {
    render(<ReplayPanel />);
    expect(api.getLatestReplay).not.toHaveBeenCalled();
  });

  it("shows a friendly message when there is no recording", async () => {
    api.getLatestReplay.mockResolvedValue(null);
    render(<ReplayPanel />);
    fireEvent.click(screen.getByRole("button", { name: /listen back/i }));
    await screen.findByText(/no recording of your last session/i);
  });

  it("shows an error message when loading fails", async () => {
    api.getLatestReplay.mockRejectedValue(new Error("boom"));
    render(<ReplayPanel />);
    fireEvent.click(screen.getByRole("button", { name: /listen back/i }));
    await screen.findByText(/couldn.t load the replay/i);
  });

  it("places a marker per flag and seeks the audio when one is clicked", async () => {
    api.getLatestReplay.mockResolvedValue(REPLAY);
    const { container } = render(<ReplayPanel />);
    fireEvent.click(screen.getByRole("button", { name: /listen back/i }));

    const marker = await screen.findByRole("button", { name: /jump to 0:30: yo tiene becomes yo tengo/i });
    expect((marker as HTMLElement).style.left).toBe("30%");
    expect((marker as HTMLElement).getAttribute("data-status")).toBe("mastered");

    fireEvent.click(marker);

    const audio = container.querySelector("audio") as HTMLAudioElement;
    expect(audio.getAttribute("src")).toBe("/review/sessions/4/audio");
    expect(audio.currentTime).toBe(28); // 30s minus the 2s lead-in
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(1);
  });
});
