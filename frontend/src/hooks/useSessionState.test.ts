import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useSessionState } from "./useSessionState";
import type { SessionStatus } from "../api/types";

// Setup mocks before importing the hook
vi.mock("../api/client", () => ({
  apiClient: {
    getStatus: vi.fn(),
    startSession: vi.fn(),
    stopSession: vi.fn(),
  },
}));

vi.mock("./useEventSource", () => ({
  useEventSource: vi.fn(() => ({
    data: null,
    connectionStatus: "open" as const,
    error: null,
  })),
}));

vi.mock("../state/store", () => ({
  useSessionStore: vi.fn((selector: any) => {
    const store = {
      status: { running: false, ready: false, graceful: null } as SessionStatus,
      transcript: [],
      setStatus: vi.fn(),
      applyEvent: vi.fn(),
    };
    return selector(store);
  }),
}));

// Now we can import after mocks are in place
import { apiClient } from "../api/client";
import { useEventSource } from "./useEventSource";
import { useSessionStore } from "../state/store";

const INITIAL_STATUS: SessionStatus = { running: false, ready: false, graceful: null };

describe("useSessionState", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Setup default mocks
    (useEventSource as any).mockReturnValue({
      data: null,
      connectionStatus: "open",
      error: null,
    });

    (useSessionStore as any).mockImplementation((selector: any) => {
      const store = {
        status: INITIAL_STATUS,
        transcript: [],
        setStatus: vi.fn(),
        applyEvent: vi.fn(),
      };
      return selector(store);
    });

    // Setup API client mocks to resolve by default
    (apiClient.getStatus as any).mockResolvedValue(INITIAL_STATUS);
    (apiClient.startSession as any).mockResolvedValue(INITIAL_STATUS);
    (apiClient.stopSession as any).mockResolvedValue(INITIAL_STATUS);
  });

  it("should initialize with status from store and no error", () => {
    const { result } = renderHook(() => useSessionState());

    expect(result.current.status).toEqual(INITIAL_STATUS);
    expect(result.current.error).toBe(null);
    expect(result.current.connectionStatus).toBe("open");
  });

  it("getStatus should call apiClient and set status on success", async () => {
    const newStatus: SessionStatus = { running: true, ready: true, graceful: null };
    const setStatusMock = vi.fn();

    (useSessionStore as any).mockImplementation((selector: any) => {
      const store = {
        status: INITIAL_STATUS,
        transcript: [],
        setStatus: setStatusMock,
        applyEvent: vi.fn(),
      };
      return selector(store);
    });

    (apiClient.getStatus as any).mockResolvedValueOnce(newStatus);

    renderHook(() => useSessionState());

    // Wait for effect to settle
    await vi.waitFor(() => {
      expect(apiClient.getStatus).toHaveBeenCalled();
    });

    expect(setStatusMock).toHaveBeenCalledWith(newStatus);
  });

  it("getStatus should set error string on failure", async () => {
    const errorMessage = "Network error";
    (apiClient.getStatus as any).mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useSessionState());

    await vi.waitFor(() => {
      expect(result.current.error).toBe(errorMessage);
    });
  });

  it("start should optimistically set running=true", async () => {
    const setStatusMock = vi.fn();
    (useSessionStore as any).mockImplementation((selector: any) => {
      const store = {
        status: INITIAL_STATUS,
        transcript: [],
        setStatus: setStatusMock,
        applyEvent: vi.fn(),
      };
      return selector(store);
    });

    (apiClient.startSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start();
    });

    expect(setStatusMock).toHaveBeenCalledWith({ running: true, ready: false, graceful: null });
  });

  it("start should rollback state on failure", async () => {
    const errorMessage = "Start failed";
    const previousStatus: SessionStatus = { running: false, ready: false, graceful: null };
    const setStatusMock = vi.fn();

    (useSessionStore as any).mockImplementation((selector: any) => {
      const store = {
        status: previousStatus,
        transcript: [],
        setStatus: setStatusMock,
        applyEvent: vi.fn(),
      };
      return selector(store);
    });

    (apiClient.startSession as any).mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start();
    });

    // Should first set optimistic state
    expect(setStatusMock).toHaveBeenCalledWith({ running: true, ready: false, graceful: null });

    // Should then rollback to previous state
    expect(setStatusMock).toHaveBeenCalledWith(previousStatus);

    // Should set error message
    expect(result.current.error).toBe(errorMessage);
  });

  it("stop should call apiClient and surface errors", async () => {
    const errorMessage = "Stop failed";
    (apiClient.stopSession as any).mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.stop();
    });

    expect(result.current.error).toBe(errorMessage);
  });

  it("stop should clear error on success", async () => {
    (apiClient.stopSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.stop();
    });

    expect(result.current.error).toBe(null);
  });

  it("start should clear error before attempting", async () => {
    (apiClient.startSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start();
    });

    expect(result.current.error).toBe(null);
  });
});
