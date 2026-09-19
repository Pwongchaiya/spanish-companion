import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ReviewView } from "./ReviewView";
import { useConnectionStore } from "../state/connectionStore";
import { useReviewFlow } from "../hooks/useReviewFlow";

vi.mock("../hooks/useReviewFlow");

const mockUseReviewFlow = vi.mocked(useReviewFlow);

function mockFlow(overrides: Partial<ReturnType<typeof useReviewFlow>>) {
  mockUseReviewFlow.mockReturnValue({
    flags: [
      {
        id: "f1",
        said: "comía",
        corrected: "comí",
        category: "Preterite vs imperfect",
        timestamp: "2026-09-17T00:00:00Z",
      },
    ],
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

describe("ReviewView explanation source excerpt", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  const selectedFlag = {
    id: "f1",
    said: "comía",
    corrected: "comí",
    category: "Preterite vs imperfect",
    timestamp: "2026-09-17T00:00:00Z",
  };

  it("renders the retrieved passage text under the source link", () => {
    mockFlow({
      selectedFlag,
      explanation: {
        explanation: "Use preterite for a completed past action.",
        source_url: "https://rae.es/preterite",
        source_excerpt: "El pretérito perfecto simple expresa acciones pasadas y acabadas.",
      },
    });
    render(<ReviewView />);

    expect(screen.getByText(/el pretérito perfecto simple expresa acciones/i)).toBeTruthy();
  });

  it("renders no excerpt block when source_excerpt is empty", () => {
    mockFlow({
      selectedFlag,
      explanation: {
        explanation: "I'm not certain on that one.",
        source_url: "",
        source_excerpt: "",
      },
    });
    render(<ReviewView />);

    expect(document.querySelector(".excerpt")).toBeNull();
  });
});

describe("ReviewView practice roleplay picker (Phase 4)", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  const selectedFlag = {
    id: "f1",
    said: "comía",
    corrected: "comí",
    category: "Preterite vs imperfect",
    timestamp: "2026-09-17T00:00:00Z",
  };

  const explanation = {
    explanation: "Use preterite for a completed past action.",
    source_url: "https://rae.es/preterite",
    source_excerpt: "El pretérito perfecto simple expresa acciones pasadas y acabadas.",
  };

  it("submits with no roleplay_slug when left on the default option", () => {
    const submitPractice = vi.fn();
    mockFlow({ selectedFlag, explanation, submitPractice });
    render(<ReviewView />);

    fireEvent.change(screen.getByLabelText("Now say it the way you meant it."), { target: { value: "comí" } });
    fireEvent.click(screen.getByRole("button", { name: "Log this" }));

    expect(submitPractice).toHaveBeenCalledWith("comí", undefined);
  });

  it("passes the picked roleplay slug through to submitPractice", () => {
    const submitPractice = vi.fn();
    mockFlow({ selectedFlag, explanation, submitPractice });
    render(<ReviewView />);

    fireEvent.change(screen.getByLabelText("Now say it the way you meant it."), { target: { value: "comí" } });
    fireEvent.change(screen.getByLabelText("Practice it in a scene (optional)"), {
      target: { value: "casual_chat" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Log this" }));

    expect(submitPractice).toHaveBeenCalledWith("comí", "casual_chat");
  });
});

describe("ReviewView after a practice attempt", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  const selectedFlag = {
    id: "f1",
    said: "comía",
    corrected: "comí",
    category: "Preterite vs imperfect",
    timestamp: "2026-09-17T00:00:00Z",
  };

  it("shows Mastered once the judge verdict is mastered:true", () => {
    mockFlow({
      selectedFlag,
      attempt: {
        flag_id: "f1",
        attempt_text: "comí",
        timestamp: "2026-09-18T00:00:00Z",
        mastered: true,
        grade: "good",
      },
    });
    render(<ReviewView />);

    expect(screen.getByText("Mastered")).toBeTruthy();
    expect(screen.getByText(/you've got this one now/i)).toBeTruthy();
  });

  it("shows Logged, not Mastered, when the verdict is still shaky", () => {
    mockFlow({
      selectedFlag,
      attempt: {
        flag_id: "f1",
        attempt_text: "como",
        timestamp: "2026-09-18T00:00:00Z",
        mastered: false,
        grade: "again",
      },
    });
    render(<ReviewView />);

    expect(screen.getByText("Logged")).toBeTruthy();
    expect(screen.queryByText("Mastered")).toBeNull();
  });

  it("shows the grade word alongside the Mastered/Logged badge", () => {
    mockFlow({
      selectedFlag,
      attempt: {
        flag_id: "f1",
        attempt_text: "como",
        timestamp: "2026-09-18T00:00:00Z",
        mastered: false,
        grade: "hard",
      },
    });
    render(<ReviewView />);

    expect(screen.getByText("(hard)")).toBeTruthy();
  });
});
