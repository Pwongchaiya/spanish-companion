import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useSessionState } from "./useSessionState";
import type { SessionStatus } from "../api/types";

// Setup mocks before importing the hook
vi.mock("../api/client", () => ({
  apiClient: {
    getStatus: vi.fn(),
    getSessionScenario: vi.fn(),
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

// useSessionState no longer runs its own backoff loop -- it delegates to
// runWithBackoff. Mocking the whole module lets us test the wiring
// (that getStatus gets handed to runWithBackoff with setStatus as the
// success callback) without re-testing backoff timing, which has its own
// suite at useBackoffRetry.test.ts.
const runWithBackoffMock = vi.fn((fn: () => Promise<unknown>, onSuccess: (r: unknown) => void) => {
  fn().then(onSuccess).catch(() => {});
  return vi.fn();
});
vi.mock("./useBackoffRetry", () => ({
  runWithBackoff: (...args: Parameters<typeof runWithBackoffMock>) => runWithBackoffMock(...args),
}));

const setDownMock = vi.fn();
const setOkMock = vi.fn();
const noteTransientIssueMock = vi.fn();
vi.mock("../state/connectionStore", () => ({
  useConnectionStore: {
    getState: vi.fn(() => ({
      phase: "ok",
      maxAttempts: 0,
      setDown: setDownMock,
      setOk: setOkMock,
      noteTransientIssue: noteTransientIssueMock,
    })),
  },
}));

const addToastMock = vi.fn();
vi.mock("../state/toastStore", () => ({
  useToastStore: {
    getState: vi.fn(() => ({
      addToast: addToastMock,
    })),
  },
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
    (apiClient.getSessionScenario as any).mockResolvedValue({
      proficiency_level: "beginner",
      focus_category: null,
      suggested_topic: null,
      recent_mistake_categories: [],
    });
    (apiClient.startSession as any).mockResolvedValue(INITIAL_STATUS);
    (apiClient.stopSession as any).mockResolvedValue(INITIAL_STATUS);
  });

  it("should initialize with status from store", () => {
    const { result } = renderHook(() => useSessionState());

    expect(result.current.status).toEqual(INITIAL_STATUS);
    expect(result.current.connectionStatus).toBe("open");
    expect((result.current as any).error).toBeUndefined();
  });

  it("getStatus should run through runWithBackoff and set status on success", async () => {
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

    await vi.waitFor(() => {
      expect(runWithBackoffMock).toHaveBeenCalledWith(expect.any(Function), setStatusMock);
    });

    await vi.waitFor(() => {
      expect(setStatusMock).toHaveBeenCalledWith(newStatus);
    });
  });

  it("fetches a session scenario suggestion while idle", async () => {
    const { result } = renderHook(() => useSessionState());

    await vi.waitFor(() => {
      expect(apiClient.getSessionScenario).toHaveBeenCalledOnce();
    });
    await vi.waitFor(() => {
      expect(result.current.scenario).toEqual({
        proficiency_level: "beginner",
        focus_category: null,
        suggested_topic: null,
        recent_mistake_categories: [],
      });
    });
  });

  it("does not fetch a scenario suggestion while a session is running", () => {
    (useSessionStore as any).mockImplementation((selector: any) => {
      const store = {
        status: { running: true, ready: true, graceful: null } as SessionStatus,
        transcript: [],
        setStatus: vi.fn(),
        applyEvent: vi.fn(),
      };
      return selector(store);
    });

    renderHook(() => useSessionState());

    expect(apiClient.getSessionScenario).not.toHaveBeenCalled();
  });

  it("start should pass an optional scenario override through to the API client", async () => {
    (apiClient.startSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start("practice ordering coffee");
    });

    expect(apiClient.startSession).toHaveBeenCalledWith("practice ordering coffee", undefined, undefined);
  });

  it("start should pass an optional session-length hint through to the API client", async () => {
    (apiClient.startSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start("practice ordering coffee", "5");
    });

    expect(apiClient.startSession).toHaveBeenCalledWith("practice ordering coffee", "5", undefined);
  });

  it("start should pass an optional pressure level through to the API client", async () => {
    (apiClient.startSession as any).mockResolvedValueOnce({});

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start("practice ordering coffee", "5", "push");
    });

    expect(apiClient.startSession).toHaveBeenCalledWith("practice ordering coffee", "5", "push");
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

  it("start should rollback state and call setDown on a banner-classified failure (500)", async () => {
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

    const error = Object.assign(new Error("Request failed: 500"), { status: 500 });
    (apiClient.startSession as any).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start();
    });

    // Should first set optimistic state
    expect(setStatusMock).toHaveBeenCalledWith({ running: true, ready: false, graceful: null });
    // Should then rollback to previous state
    expect(setStatusMock).toHaveBeenCalledWith(previousStatus);
    // Banner-classified error escalates to the connection store, not a toast
    expect(setDownMock).toHaveBeenCalledWith(expect.any(String), undefined, expect.any(Function));
    expect(addToastMock).not.toHaveBeenCalled();
  });

  it("start should toast on a 4xx failure with no server body (fallback message)", async () => {
    const error = Object.assign(new Error("Request failed: 404"), { status: 404 });
    (apiClient.startSession as any).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.start();
    });

    expect(addToastMock).toHaveBeenCalledWith(
      "Couldn't start the conversation.",
      expect.objectContaining({ retry: expect.any(Function) }),
    );
    expect(setDownMock).not.toHaveBeenCalled();
  });

  it("stop should call setDown on a banner-classified failure", async () => {
    const error = Object.assign(new Error("Request failed: 503"), { status: 503 });
    (apiClient.stopSession as any).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.stop();
    });

    expect(setDownMock).toHaveBeenCalledWith(expect.any(String), undefined, expect.any(Function));
  });

  it("stop should toast on a 4xx failure with a real server message", async () => {
    const error = Object.assign(new Error("Session not found"), { status: 404 });
    (apiClient.stopSession as any).mockRejectedValueOnce(error);

    const { result } = renderHook(() => useSessionState());

    await act(async () => {
      await result.current.stop();
    });

    expect(addToastMock).toHaveBeenCalledWith(
      "Couldn't stop the conversation.",
      expect.objectContaining({ retry: expect.any(Function) }),
    );
  });
});
