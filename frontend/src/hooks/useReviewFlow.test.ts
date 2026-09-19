import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../api/client", () => ({
  apiClient: {
    listFlags: vi.fn(),
    getTaskOutcome: vi.fn(() => Promise.resolve(null)),
    explainFlag: vi.fn(),
    submitPractice: vi.fn(),
  },
}));

vi.mock("./useBackoffRetry", () => ({
  runWithBackoff: vi.fn(() => vi.fn()),
}));

vi.mock("../api/errorClassification", () => ({
  classifyError: vi.fn(),
}));

const addToastMock = vi.fn();
vi.mock("../state/toastStore", () => ({
  useToastStore: (selector: any) => selector({ addToast: addToastMock }),
}));

const setDownMock = vi.fn();
vi.mock("../state/connectionStore", () => ({
  useConnectionStore: { getState: () => ({ setDown: setDownMock }) },
}));

import { useReviewFlow } from "./useReviewFlow";
import { apiClient } from "../api/client";
import { runWithBackoff } from "./useBackoffRetry";
import { classifyError } from "../api/errorClassification";

describe("useReviewFlow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads flags via runWithBackoff, never toasting on background-read failure", () => {
    renderHook(() => useReviewFlow());

    expect(runWithBackoff).toHaveBeenCalledTimes(1);
    const [fn, , message, subMessage] = (runWithBackoff as any).mock.calls[0];
    expect(fn).toBeInstanceOf(Function);
    expect(message).toBe("Having trouble reaching the server.");
    expect(subMessage).toBe("These are the flags from last time, held locally.");
    expect(addToastMock).not.toHaveBeenCalled();
  });

  it("routes a field-classified selectFlag error into hook error state", async () => {
    const err = Object.assign(new Error("Flag not found"), { status: 404 });
    (apiClient.explainFlag as any).mockRejectedValue(err);
    (classifyError as any).mockReturnValue({ kind: "field", message: "Flag not found" });

    const { result } = renderHook(() => useReviewFlow());
    await act(async () => {
      await result.current.selectFlag("f1");
    });

    expect(result.current.error).toBe("Flag not found");
    expect(addToastMock).not.toHaveBeenCalled();
    expect(setDownMock).not.toHaveBeenCalled();
  });

  it("routes a toast-classified submitPractice error into addToast", async () => {
    // seed a selected flag first
    (apiClient.explainFlag as any).mockResolvedValue({ explanation: "x", source_url: "y" });
    const err = Object.assign(new Error("Request failed: 400"), { status: 400 });
    (apiClient.submitPractice as any).mockRejectedValue(err);
    (classifyError as any).mockReturnValue({ kind: "toast", message: "Request failed: 400" });

    const { result } = renderHook(() => useReviewFlow());
    await act(async () => {
      await result.current.selectFlag("f1");
    });
    await act(async () => {
      await result.current.submitPractice("hola");
    });

    expect(addToastMock).toHaveBeenCalledWith(
      "Couldn't save that practice attempt.",
      expect.objectContaining({ subMessage: "Your answer is still in the box.", retry: expect.any(Function) }),
    );
    expect(result.current.error).toBeNull();
    expect(setDownMock).not.toHaveBeenCalled();
  });

  it("routes a banner-classified error into connectionStore.setDown", async () => {
    const err = Object.assign(new Error("boom"), { status: 502 });
    (apiClient.explainFlag as any).mockRejectedValue(err);
    (classifyError as any).mockReturnValue({ kind: "banner", immediate: false });

    const { result } = renderHook(() => useReviewFlow());
    await act(async () => {
      await result.current.selectFlag("f1");
    });

    expect(setDownMock).toHaveBeenCalledTimes(1);
    const [message, subMessage, retry] = setDownMock.mock.calls[0];
    expect(message).toBe("Having trouble reaching the server.");
    expect(subMessage).toBeUndefined();
    expect(retry).toBeInstanceOf(Function);
    expect(addToastMock).not.toHaveBeenCalled();
  });
});
