import { describe, it, expect, beforeEach } from "vitest";
import { useConnectionStore } from "./connectionStore";

describe("connectionStore", () => {
  beforeEach(() => {
    useConnectionStore.setState({
      phase: "ok",
      attempt: 0,
      maxAttempts: 0,
      message: "",
      subMessage: undefined,
      retry: null,
    });
  });

  it("starts ok", () => {
    expect(useConnectionStore.getState().phase).toBe("ok");
  });

  it("setRetrying moves to retrying with the given attempt/maxAttempts", () => {
    useConnectionStore.getState().setRetrying(2, 4);
    const s = useConnectionStore.getState();
    expect(s.phase).toBe("retrying");
    expect(s.attempt).toBe(2);
    expect(s.maxAttempts).toBe(4);
  });

  it("setDown moves to down with message/subMessage/retry", () => {
    const retry = () => {};
    useConnectionStore.getState().setDown("Having trouble reaching the server.", "hint", retry);
    const s = useConnectionStore.getState();
    expect(s.phase).toBe("down");
    expect(s.message).toBe("Having trouble reaching the server.");
    expect(s.subMessage).toBe("hint");
    expect(s.retry).toBe(retry);
  });

  it("setOk resets every field back to the ok baseline", () => {
    useConnectionStore.getState().setDown("msg", "sub", () => {});
    useConnectionStore.getState().setOk();
    const s = useConnectionStore.getState();
    expect(s).toMatchObject({ phase: "ok", attempt: 0, maxAttempts: 0, message: "", subMessage: undefined, retry: null });
  });

  it("noteTransientIssue moves ok -> retrying(0,0)", () => {
    useConnectionStore.getState().noteTransientIssue();
    const s = useConnectionStore.getState();
    expect(s.phase).toBe("retrying");
    expect(s.maxAttempts).toBe(0);
  });

  it("noteTransientIssue does not clobber an in-progress backoff sequence", () => {
    useConnectionStore.getState().setRetrying(3, 4);
    useConnectionStore.getState().noteTransientIssue();
    const s = useConnectionStore.getState();
    expect(s.attempt).toBe(3);
    expect(s.maxAttempts).toBe(4);
  });

  it("noteTransientIssue does not override an already-down state", () => {
    useConnectionStore.getState().setDown("down msg", undefined, null);
    useConnectionStore.getState().noteTransientIssue();
    expect(useConnectionStore.getState().phase).toBe("down");
  });
});
