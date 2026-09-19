import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRecorder, MAX_RECORD_MS } from "./useRecorder";

class FakeRecorder {
  static supported = ["audio/webm"];
  static isTypeSupported = (m: string) => FakeRecorder.supported.includes(m);
  static last: FakeRecorder;
  state: "inactive" | "recording" = "inactive";
  mimeType: string;
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  opts?: { mimeType?: string };
  constructor(_stream: MediaStream, opts?: { mimeType?: string }) {
    this.opts = opts;
    this.mimeType = opts?.mimeType ?? "";
    FakeRecorder.last = this;
  }
  start() {
    this.state = "recording";
  }
  stop() {
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob(["x"]) });
    this.onstop?.();
  }
}

const trackStop = vi.fn();

function mockGetUserMedia(impl: () => Promise<MediaStream>) {
  Object.defineProperty(navigator, "mediaDevices", { value: { getUserMedia: vi.fn(impl) }, configurable: true });
}

describe("useRecorder", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    trackStop.mockClear();
    FakeRecorder.supported = ["audio/webm"];
    vi.stubGlobal("MediaRecorder", FakeRecorder);
    mockGetUserMedia(async () => ({ getTracks: () => [{ stop: trackStop }] }) as unknown as MediaStream);
  });
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("records, then stop yields a blob, status done, tracks stopped", async () => {
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    expect(result.current.status).toBe("recording");
    expect(FakeRecorder.last.opts?.mimeType).toBe("audio/webm");

    act(() => result.current.stop());
    expect(result.current.status).toBe("done");
    expect(result.current.blob).toBeInstanceOf(Blob);
    expect(trackStop).toHaveBeenCalledTimes(1);
  });

  it("auto-stops after MAX_RECORD_MS", async () => {
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    act(() => void vi.advanceTimersByTime(MAX_RECORD_MS));
    expect(result.current.status).toBe("done");
  });

  it("NotAllowedError sets status error with a permission message", async () => {
    mockGetUserMedia(async () => {
      throw new DOMException("blocked", "NotAllowedError");
    });
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    expect(result.current.status).toBe("error");
    expect(result.current.error).toMatch(/permission/i);
  });

  it("other failure surfaces its message", async () => {
    mockGetUserMedia(async () => {
      throw new DOMException("no mic found", "NotFoundError");
    });
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    expect(result.current.status).toBe("error");
    expect(result.current.error).toContain("no mic found");
  });

  it("falls back to default mimeType when none is supported", async () => {
    FakeRecorder.supported = [];
    const { result } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    expect(FakeRecorder.last.opts).toBeUndefined();
  });

  it("stops tracks on unmount while recording", async () => {
    const { result, unmount } = renderHook(() => useRecorder());
    await act(() => result.current.start());
    unmount();
    expect(trackStop).toHaveBeenCalledTimes(1);
  });
});
