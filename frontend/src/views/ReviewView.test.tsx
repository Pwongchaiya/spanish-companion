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
    taskOutcome: null,
    sessionRecap: null,
    replayDurationSeconds: null,
    mistakeSummary: [],
    practicePhase: "idle",
    lastRecordedSeconds: null,
    setPracticePhase: vi.fn(),
    selectFlag: vi.fn(),
    submitPractice: vi.fn(),
    submitSpokenPractice: vi.fn(),
    updateFlagStatus: vi.fn(),
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

  it("hides the offline banner when the connection is ok", () => {
    mockFlow({});
    render(<ReviewView />);

    expect(screen.queryByText(/explanations and grading come from the server/i)).toBeNull();
  });

  it("shows the offline banner once the backend is unreachable, given a cached list", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockFlow({});
    render(<ReviewView />);

    expect(screen.getByText(/explanations and grading come from the server, so those wait/i)).toBeTruthy();
  });
});

describe("ReviewView when listFlags has never succeeded", () => {
  it("shows a not-loaded message instead of the stale empty-list copy while the backend is down", () => {
    useConnectionStore.getState().setDown("Having trouble reaching the server.", undefined, vi.fn());
    mockFlow({ flags: [], hasLoaded: false });
    render(<ReviewView />);

    expect(screen.getByText("Can’t check for flags right now.")).toBeTruthy();
    expect(screen.queryByText(/nothing was flagged last time/i)).toBeNull();
  });

  it("still shows the genuine empty-list message once a successful load confirms there's nothing flagged", () => {
    useConnectionStore.getState().setOk();
    mockFlow({ flags: [], hasLoaded: true });
    render(<ReviewView />);

    expect(screen.getByText(/nothing was flagged last time/i)).toBeTruthy();
    expect(screen.queryByText("Can’t check for flags right now.")).toBeNull();
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

describe("ReviewView practice roleplay picker", () => {
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
    mockFlow({ selectedFlag, explanation, practicePhase: "typed", submitPractice });
    render(<ReviewView />);

    fireEvent.change(screen.getByLabelText("Type your answer"), { target: { value: "comí" } });
    fireEvent.click(screen.getByRole("button", { name: "Log this" }));

    expect(submitPractice).toHaveBeenCalledWith("comí", undefined);
  });

  it("passes the picked roleplay slug through to submitPractice", () => {
    const submitPractice = vi.fn();
    mockFlow({ selectedFlag, explanation, practicePhase: "typed", submitPractice });
    render(<ReviewView />);

    fireEvent.change(screen.getByLabelText("Type your answer"), { target: { value: "comí" } });
    fireEvent.change(screen.getByLabelText("Scene"), { target: { value: "casual_chat" } });
    fireEvent.click(screen.getByRole("button", { name: "Log this" }));

    expect(submitPractice).toHaveBeenCalledWith("comí", "casual_chat");
  });
});

describe("ReviewView spoken practice phases", () => {
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
    source_excerpt: "",
  };

  it("shows the no-speech notice and does not offer to log anything unsaid", () => {
    mockFlow({ selectedFlag, explanation, practicePhase: "nospeech" });
    render(<ReviewView />);

    expect(screen.getByText(/nothing came through/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /record again/i })).toBeTruthy();
  });

  it("offers a typed fallback input while the mic is blocked", () => {
    mockFlow({ selectedFlag, explanation, practicePhase: "denied" });
    render(<ReviewView />);

    expect(screen.getByText("Microphone blocked")).toBeTruthy();
    expect(screen.getByRole("button", { name: /type it instead/i })).toBeTruthy();
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
    expect(screen.getByText(/this pattern is marked resolved/i)).toBeTruthy();
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

describe("ReviewView task-outcome badge", () => {
  beforeEach(() => {
    useConnectionStore.getState().setOk();
  });

  const base = { scenario_slug: "ordering_coffee", label: "Ordering coffee", success_condition: "orders both" };

  it("shows nothing when the last session had no task scenario", () => {
    mockFlow({ taskOutcome: null });
    render(<ReviewView />);

    expect(screen.queryByText(/Task complete|Task not completed|Not judged yet/)).toBeNull();
  });

  it("shows a success badge", () => {
    mockFlow({ taskOutcome: { ...base, outcome: "success" } });
    render(<ReviewView />);

    expect(screen.getByText(/Ordering coffee:/)).toBeTruthy();
    expect(screen.getByText(/Task complete/)).toBeTruthy();
  });

  it("shows a fail badge", () => {
    mockFlow({ taskOutcome: { ...base, outcome: "fail" } });
    render(<ReviewView />);

    expect(screen.getByText(/Task not completed/)).toBeTruthy();
  });

  it("shows a pending badge when the outcome is not judged yet", () => {
    mockFlow({ taskOutcome: { ...base, outcome: null } });
    render(<ReviewView />);

    expect(screen.getByText(/Not judged yet/)).toBeTruthy();
  });
});

describe("ReviewView mastered/skipped status", () => {
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
  const explanation = { explanation: "x", source_url: "y", source_excerpt: "" };

  it("calls updateFlagStatus with mastered when the Mark mastered action is clicked", () => {
    const updateFlagStatus = vi.fn();
    mockFlow({ selectedFlag, explanation, updateFlagStatus });
    render(<ReviewView />);

    fireEvent.click(screen.getByRole("button", { name: /mark mastered/i }));

    expect(updateFlagStatus).toHaveBeenCalledWith("f1", "mastered");
  });

  it("calls updateFlagStatus with skipped when the Skip for now action is clicked", () => {
    const updateFlagStatus = vi.fn();
    mockFlow({ selectedFlag, explanation, updateFlagStatus });
    render(<ReviewView />);

    fireEvent.click(screen.getByRole("button", { name: /skip for now/i }));

    expect(updateFlagStatus).toHaveBeenCalledWith("f1", "skipped");
  });
});
