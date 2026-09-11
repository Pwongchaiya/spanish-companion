import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ReviewView } from "./ReviewView";
import { useConnectionStore } from "../state/connectionStore";
import { useReviewFlow } from "../hooks/useReviewFlow";

vi.mock("../hooks/useReviewFlow");

const mockUseReviewFlow = vi.mocked(useReviewFlow);

function mockFlow(overrides: Partial<ReturnType<typeof useReviewFlow>>) {
  mockUseReviewFlow.mockReturnValue({
    flags: [{ id: "f1", said: "comía", corrected: "comí", category: "Preterite vs imperfect" }],
    hasLoaded: true,
    selectedFlag: null,
    explanation: null,
    attempt: null,
    error: null,
    selectFlag: vi.fn(),
    submitPractice: vi.fn(),
    backToList: vi.fn(),
    ...overrides,
  });
}

describe("ReviewView flag list during an outage", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  it("keeps flag rows enabled when the connection is ok", () => {
    mockFlow({});
    render(<ReviewView />);

    expect(screen.getByRole("button", { name: /comía/i }).hasAttribute("disabled")).toBe(false);
  });

  it("disables flag rows once the backend is unreachable", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockFlow({});
    render(<ReviewView />);

    expect(screen.getByRole("button", { name: /comía/i }).hasAttribute("disabled")).toBe(true);
  });

  it("hides the outage hint when the connection is ok", () => {
    mockFlow({});
    render(<ReviewView />);

    expect(screen.queryByText(/explanations come from the server/i)).toBeNull();
  });

  it("shows the outage hint once the backend is unreachable, given a cached list", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockFlow({});
    render(<ReviewView />);

    expect(screen.getByText(/explanations come from the server, so those wait/i)).toBeTruthy();
  });
});

describe("ReviewView when listFlags has never succeeded", () => {
  it("shows a not-loaded message instead of the stale empty-list copy while the backend is down", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockFlow({ flags: [], hasLoaded: false });
    render(<ReviewView />);

    expect(screen.getByText("Can’t check for flags right now.")).toBeTruthy();
    expect(screen.queryByText(/nothing was flagged last time/i)).toBeNull();
    expect(screen.queryByText(/you can read the list/i)).toBeNull();
  });

  it("still shows the genuine empty-list message once a successful load confirms there's nothing flagged", () => {
    useConnectionStore.getState().setOk();
    mockFlow({ flags: [], hasLoaded: true });
    render(<ReviewView />);

    expect(screen.getByText(/nothing was flagged last time/i)).toBeTruthy();
    expect(screen.queryByText(/can't check for flags/i)).toBeNull();
  });
});
