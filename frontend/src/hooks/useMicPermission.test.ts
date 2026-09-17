import { describe, it, expect, vi } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useMicPermission } from "./useMicPermission";

function mockGetUserMedia(impl: () => Promise<MediaStream>) {
  Object.defineProperty(navigator, "mediaDevices", {
    value: { getUserMedia: vi.fn(impl) },
    configurable: true,
  });
}

describe("useMicPermission", () => {
  it("granted: stops the track and sets status granted", async () => {
    const stop = vi.fn();
    mockGetUserMedia(async () => ({ getTracks: () => [{ stop }] }) as unknown as MediaStream);

    const { result } = renderHook(() => useMicPermission());
    act(() => void result.current.requestMic());

    await waitFor(() => expect(result.current.status).toBe("granted"));
    expect(stop).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
  });

  it("denied: NotAllowedError sets status denied", async () => {
    mockGetUserMedia(async () => {
      throw new DOMException("blocked", "NotAllowedError");
    });

    const { result } = renderHook(() => useMicPermission());
    act(() => void result.current.requestMic());

    await waitFor(() => expect(result.current.status).toBe("denied"));
  });

  it("other failure (e.g. no device) sets status error, not denied", async () => {
    mockGetUserMedia(async () => {
      throw new DOMException("no mic found", "NotFoundError");
    });

    const { result } = renderHook(() => useMicPermission());
    act(() => void result.current.requestMic());

    await waitFor(() => expect(result.current.status).toBe("error"));
  });
});
