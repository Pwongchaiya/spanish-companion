import { useState } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ErrorBoundary } from "./ErrorBoundary";

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error("boom");
  return <p>fine</p>;
}

describe("ErrorBoundary", () => {
  it("renders children when nothing throws", () => {
    render(
      <ErrorBoundary>
        <Bomb shouldThrow={false} />
      </ErrorBoundary>,
    );
    expect(screen.getByText("fine")).toBeTruthy();
  });

  it("renders fallback UI with the error message when a child throws", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <Bomb shouldThrow={true} />
      </ErrorBoundary>,
    );

    expect(screen.getByText("Something went wrong")).toBeTruthy();
    expect(screen.getByText("boom")).toBeTruthy();

    vi.restoreAllMocks();
  });

  it("reset button re-renders children once the thrown condition clears", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    function Wrapper() {
      const [shouldThrow, setShouldThrow] = useState(true);
      return (
        <div>
          <button onClick={() => setShouldThrow(false)}>fix</button>
          <ErrorBoundary>
            <Bomb shouldThrow={shouldThrow} />
          </ErrorBoundary>
        </div>
      );
    }

    render(<Wrapper />);
    expect(screen.getByText("Something went wrong")).toBeTruthy();

    // Fix the underlying condition, then use the boundary's own reset
    // action to re-attempt rendering children.
    fireEvent.click(screen.getByText("fix"));
    fireEvent.click(screen.getByText("Try again"));

    expect(screen.getByText("fine")).toBeTruthy();

    vi.restoreAllMocks();
  });
});
