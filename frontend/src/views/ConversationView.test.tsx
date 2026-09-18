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

  it("keeps the plain hint when no scenario has loaded yet", () => {
    mockSession({ status: { running: false, ready: false, graceful: null }, scenario: null });
    render(<ConversationView />);

    expect(screen.getByText(/press start and talk/i)).toBeTruthy();
    expect(screen.queryByLabelText("Session scenario")).toBeNull();
  });

  it("shows an editable field pre-filled from the suggestion once loaded", () => {
    mockSession({
      status: { running: false, ready: false, graceful: null },
      scenario: {
        proficiency_level: "beginner",
        focus_category: null,
        suggested_topic: "ordering coffee",
        recent_mistake_categories: [],
      },
    });
    render(<ConversationView />);

    expect(screen.queryByText(/press start and talk/i)).toBeNull();
    const field = screen.getByLabelText("Session scenario") as HTMLTextAreaElement;
    expect(field.value).toBe("Speak at a beginner proficiency level. Focus this session on: ordering coffee.");
  });

  it("passes the (possibly edited) scenario text to start()", () => {
    const startMock = vi.fn();
    mockSession({
      status: { running: false, ready: false, graceful: null },
      scenario: {
        proficiency_level: "beginner",
        focus_category: null,
        suggested_topic: "ordering coffee",
        recent_mistake_categories: [],
      },
      start: startMock,
    });
    render(<ConversationView />);

    const field = screen.getByLabelText("Session scenario");
    fireEvent.change(field, { target: { value: "talk about the weather" } });
    fireEvent.click(screen.getByRole("button", { name: "Start" }));

    expect(startMock).toHaveBeenCalledWith("talk about the weather");
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
