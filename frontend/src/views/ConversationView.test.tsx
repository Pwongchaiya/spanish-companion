import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ConversationView } from "./ConversationView";
import { useConnectionStore } from "../state/connectionStore";
import { useSessionState } from "../hooks/useSessionState";

vi.mock("../hooks/useSessionState");

const mockUseSessionState = vi.mocked(useSessionState);

function mockSession(overrides: Partial<ReturnType<typeof useSessionState>>) {
  mockUseSessionState.mockReturnValue({
    status: { running: false, ready: false, graceful: null },
    transcript: [],
    turnState: null,
    connectionStatus: "open",
    scenario: null,
    start: vi.fn(),
    stop: vi.fn(),
    ...overrides,
  });
}

describe("ConversationView idle state", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  it("hides the status label when stopped, but still shows the hint and Start", () => {
    mockSession({ status: { running: false, ready: false, graceful: null } });
    render(<ConversationView />);

    expect(screen.queryByText(/stopped/i)).toBeNull();
    expect(screen.getByText(/press start and talk/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Start" })).toBeTruthy();
  });

  it("shows the status label once running", () => {
    mockSession({
      status: { running: true, ready: true, graceful: null },
      turnState: "listening",
    });
    render(<ConversationView />);

    expect(screen.getByText("Listening")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Stop" })).toBeTruthy();
  });

  it("hides the hint once a transcript exists", () => {
    mockSession({
      status: { running: true, ready: true, graceful: null },
      turnState: "listening",
      transcript: [{ role: "user", text: "Hola" }],
    });
    render(<ConversationView />);

    expect(screen.queryByText(/press start and talk/i)).toBeNull();
  });
});

describe("ConversationView scenario picker", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  const loadedScenario = {
    proficiency_level: "beginner",
    focus_category: null,
    suggested_topic: "ordering coffee",
    recent_mistake_categories: [],
  };

  it("keeps the plain hint when no scenario has loaded yet", () => {
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: null });
    render(<ConversationView />);

    expect(screen.getByText(/press start and talk/i)).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Pressure" })).toBeNull();
  });

  it("shows the pressure dial, defaulted to Normal, once a scenario loads", () => {
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: loadedScenario });
    render(<ConversationView />);

    expect(screen.queryByText(/press start and talk/i)).toBeNull();
    expect(screen.getByRole("button", { name: "Normal" }).getAttribute("aria-pressed")).toBe("true");
    // The reveal link, not the panel contents, is what's gone once opened.
    expect(screen.getByRole("button", { name: "+ More to adjust" })).toBeTruthy();
  });

  it("composes the pressure phrase plus scene text and passes it to start() on Start", () => {
    const startMock = vi.fn();
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: loadedScenario, start: startMock });
    render(<ConversationView />);

    fireEvent.click(screen.getByRole("button", { name: "+ More to adjust" }));
    fireEvent.change(screen.getByLabelText(/set the scene/i), { target: { value: "talk about the weather" } });
    fireEvent.click(screen.getByRole("button", { name: "Push" }));
    fireEvent.click(screen.getByRole("button", { name: "Start" }));

    expect(startMock).toHaveBeenCalledWith("Push me. talk about the weather", undefined);
  });

  it("passes the selected session length as a hint, and Done/Start both collapse the panel", () => {
    const startMock = vi.fn();
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: loadedScenario, start: startMock });
    render(<ConversationView />);

    fireEvent.click(screen.getByRole("button", { name: "+ More to adjust" }));
    fireEvent.click(screen.getByRole("button", { name: "5 min" }));
    fireEvent.click(screen.getByRole("button", { name: "Done" }));

    // Panel closed by Done -- the reveal link is back.
    expect(screen.getByRole("button", { name: "+ More to adjust" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Start" }));
    expect(startMock).toHaveBeenCalledWith(expect.any(String), "5");
  });
});

describe("ConversationView mic control (P2 placement)", () => {
  const loadedScenario = {
    proficiency_level: "beginner",
    focus_category: null,
    suggested_topic: "ordering coffee",
    recent_mistake_categories: [],
  };

  beforeEach(() => {
    useConnectionStore.getState().setOk();
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: loadedScenario });
  });

  it("lives inside the more-adjust panel, not as its own standalone button", () => {
    render(<ConversationView />);
    expect(screen.queryByRole("button", { name: "Request mic access" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "+ More to adjust" }));
    expect(screen.getByRole("button", { name: "Grant access" })).toBeTruthy();
  });

  it("requests mic access and shows Ready once granted", async () => {
    const getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [] });
    vi.stubGlobal("navigator", { ...navigator, mediaDevices: { getUserMedia } });

    render(<ConversationView />);
    fireEvent.click(screen.getByRole("button", { name: "+ More to adjust" }));
    fireEvent.click(screen.getByRole("button", { name: "Grant access" }));

    expect(getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(await screen.findByRole("button", { name: "Ready" })).toBeTruthy();

    vi.unstubAllGlobals();
  });

  it("badges the closed reveal link when access is denied", async () => {
    const denial = new DOMException("no", "NotAllowedError");
    const getUserMedia = vi.fn().mockRejectedValue(denial);
    vi.stubGlobal("navigator", { ...navigator, mediaDevices: { getUserMedia } });

    render(<ConversationView />);
    fireEvent.click(screen.getByRole("button", { name: "+ More to adjust" }));
    fireEvent.click(screen.getByRole("button", { name: "Grant access" }));
    expect(await screen.findByRole("button", { name: "Blocked — retry" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(screen.getByText("· Needs mic")).toBeTruthy();

    vi.unstubAllGlobals();
  });
});

describe("ConversationView connection-degraded states", () => {
  it("hides the Start/Stop button entirely while quietly retrying", () => {
    useConnectionStore.getState().setRetrying(2, 4);
    mockSession({ status: { running: true, ready: true, graceful: null } });
    render(<ConversationView />);

    expect(screen.getByText("Holding")).toBeTruthy();
    expect(screen.getByText(/your last conversation is still here/i)).toBeTruthy();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("shows a disabled button once retries are exhausted", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockSession({ status: { running: true, ready: true, graceful: null } });
    render(<ConversationView />);

    expect(screen.getByText("Offline")).toBeTruthy();
    expect(screen.getByText(/reading this one doesn't/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Stop" }).hasAttribute("disabled")).toBe(true);
  });
});
