import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { runWithBackoff } from "./useBackoffRetry";
import { useConnectionStore } from "../state/connectionStore";
import type { ApiClientError } from "../api/client";

function err(status?: number): ApiClientError {
  const e = new Error(status ? `Request failed: ${status}` : "Failed to fetch") as ApiClientError;
  e.status = status;
  return e;
}

describe("runWithBackoff", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    useConnectionStore.setState({ phase: "ok", attempt: 0, maxAttempts: 0, message: "", subMessage: undefined, retry: null });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("resolves immediately on first success, store stays ok", async () => {
    const onSuccess = vi.fn();
    const fn = vi.fn().mockResolvedValue("ok-result");

    runWithBackoff(fn, onSuccess);
    await vi.waitFor(() => expect(onSuccess).toHaveBeenCalledWith("ok-result"));

    expect(fn).toHaveBeenCalledTimes(1);
    expect(useConnectionStore.getState().phase).toBe("ok");
  });

  it("500 escalates to down immediately, no retry attempted", async () => {
    const fn = vi.fn().mockRejectedValue(err(500));

    runWithBackoff(fn, vi.fn());
    await vi.waitFor(() => expect(useConnectionStore.getState().phase).toBe("down"));

    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("502 retries with backoff, then escalates to down after 4 attempts", async () => {
    const fn = vi.fn().mockRejectedValue(err(502));

    runWithBackoff(fn, vi.fn());

    await vi.waitFor(() => expect(useConnectionStore.getState()).toMatchObject({ phase: "retrying", attempt: 1, maxAttempts: 4 }));

    await vi.advanceTimersByTimeAsync(1000);
    await vi.waitFor(() => expect(useConnectionStore.getState().attempt).toBe(2));

    await vi.advanceTimersByTimeAsync(2000);
    await vi.waitFor(() => expect(useConnectionStore.getState().attempt).toBe(3));

    await vi.advanceTimersByTimeAsync(4000);
    await vi.waitFor(() => expect(useConnectionStore.getState().attempt).toBe(4));

    await vi.advanceTimersByTimeAsync(8000);
    await vi.waitFor(() => expect(useConnectionStore.getState().phase).toBe("down"));

    expect(fn).toHaveBeenCalledTimes(5);
  });

  it("down state's retry callback restarts the attempt sequence from 1", async () => {
    const fn = vi.fn().mockRejectedValue(err(500));

    runWithBackoff(fn, vi.fn());
    await vi.waitFor(() => expect(useConnectionStore.getState().phase).toBe("down"));

    const retry = useConnectionStore.getState().retry;
    expect(retry).not.toBeNull();

    retry?.();
    await vi.waitFor(() => expect(fn).toHaveBeenCalledTimes(2));
  });

  it("cancel stops further attempts after unmount", async () => {
    const fn = vi.fn().mockRejectedValue(err(502));

    const cancel = runWithBackoff(fn, vi.fn());
    await vi.waitFor(() => expect(useConnectionStore.getState().phase).toBe("retrying"));

    cancel();
    const callsBeforeAdvance = fn.mock.calls.length;

    await vi.advanceTimersByTimeAsync(10000);
    expect(fn).toHaveBeenCalledTimes(callsBeforeAdvance);
  });
});
