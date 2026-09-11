import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ToastContainer } from "./Toast";
import { useToastStore } from "../state/toastStore";

describe("ToastContainer", () => {
  beforeEach(() => {
    useToastStore.setState({ toasts: [] });
  });

  it("renders nothing when there are no toasts", () => {
    const { container } = render(<ToastContainer />);
    expect(container.firstChild).toBeNull();
  });

  it("renders message, subMessage, and count for a deduped toast", () => {
    useToastStore.getState().addToast("Couldn't save that practice attempt.", {
      subMessage: "Your answer is still in the box.",
    });
    useToastStore.getState().addToast("Couldn't save that practice attempt.", {
      subMessage: "Your answer is still in the box.",
    });

    render(<ToastContainer />);
    expect(screen.getByText("Couldn't save that practice attempt.")).toBeTruthy();
    expect(screen.getByText("Your answer is still in the box.")).toBeTruthy();
    expect(screen.getByText("2×")).toBeTruthy();
  });

  it("only shows a Try again button when a retry callback was supplied", () => {
    useToastStore.getState().addToast("No retry here");
    render(<ToastContainer />);
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });

  it("Try again calls retry and dismisses the toast", () => {
    const retry = vi.fn();
    useToastStore.getState().addToast("Couldn't save that practice attempt.", { retry });

    render(<ToastContainer />);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(retry).toHaveBeenCalledOnce();
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });
});
