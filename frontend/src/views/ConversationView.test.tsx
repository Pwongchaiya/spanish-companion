import { render, screen } from "@testing-library/react";
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
