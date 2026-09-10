import { describe, it, expect, beforeEach } from "vitest";
import { useToastStore } from "./toastStore";

describe("toastStore", () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it("starts with no toasts", () => {
    expect(useToastStore.getState().toasts).toEqual([]);
  });

  it("addToast appends a toast with a unique id", () => {
    useToastStore.getState().addToast("first");
    useToastStore.getState().addToast("second");

    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(2);
    expect(toasts[0].message).toBe("first");
    expect(toasts[1].message).toBe("second");
    expect(toasts[0].id).not.toBe(toasts[1].id);
  });

  it("dismissToast removes only the matching toast", () => {
    useToastStore.getState().addToast("keep me");
    useToastStore.getState().addToast("remove me");

    const [, second] = useToastStore.getState().toasts;
    useToastStore.getState().dismissToast(second.id);

    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(1);
    expect(toasts[0].message).toBe("keep me");
  });

  it("addToast dedupes an identical message into one toast with a bumped count", () => {
    useToastStore.getState().addToast("Couldn't load flagged errors: Request failed: 502");
    useToastStore.getState().addToast("Couldn't load flagged errors: Request failed: 502");
    useToastStore.getState().addToast("Couldn't load flagged errors: Request failed: 502");

    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(1);
    expect(toasts[0].count).toBe(3);
  });

  it("addToast starts a fresh toast at count 1 for a different message", () => {
    useToastStore.getState().addToast("first");
    useToastStore.getState().addToast("second");

    const { toasts } = useToastStore.getState();
    expect(toasts).toHaveLength(2);
    expect(toasts[0].count).toBe(1);
    expect(toasts[1].count).toBe(1);
  });
});
