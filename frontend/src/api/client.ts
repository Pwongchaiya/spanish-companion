import type {
  Explanation,
  Flag,
  MistakePatternSummary,
  PracticeAttempt,
  PronunciationResult,
  PronunciationTrendPoint,
  SessionRecap,
  SessionScenario,
  SessionStatus,
  SpeakingTotal,
  TopicCoverageEntry,
  UnflaggedStreak,
} from "./types";

export type ApiClientError = Error & { status?: number };

function createApiClientError(message: string, status?: number): ApiClientError {
  const error = new Error(message) as ApiClientError;
  error.status = status;
  return error;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const message = (body as { error?: string }).error ?? `Request failed: ${res.status}`;
    throw createApiClientError(message, res.status);
  }
  return res.json() as Promise<T>;
}

export const apiClient = {
  getStatus: (): Promise<SessionStatus> => fetch("/status").then(json<SessionStatus>),
  getSessionScenario: (): Promise<SessionScenario> => fetch("/session-scenario").then(json<SessionScenario>),
  startSession: (scenarioText?: string, sessionLengthHint?: string, pressureLevel?: string): Promise<SessionStatus> =>
    fetch("/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_text: scenarioText,
        session_length_hint: sessionLengthHint,
        pressure_level: pressureLevel,
      }),
    }).then(json<SessionStatus>),
  stopSession: (): Promise<SessionStatus> => fetch("/stop", { method: "POST" }).then(json<SessionStatus>),

  listFlags: (): Promise<Flag[]> => fetch("/review/flags").then(json<Flag[]>),
  listMistakeSummary: (): Promise<MistakePatternSummary[]> =>
    fetch("/progress/mistakes").then(json<MistakePatternSummary[]>),
  listTopicCoverage: (): Promise<TopicCoverageEntry[]> => fetch("/progress/topics").then(json<TopicCoverageEntry[]>),
  getSpeakingTotal: (): Promise<SpeakingTotal> => fetch("/progress/speaking").then(json<SpeakingTotal>),
  getUnflaggedStreak: (): Promise<UnflaggedStreak> => fetch("/progress/streak").then(json<UnflaggedStreak>),
  getSessionRecap: (): Promise<SessionRecap | null> => fetch("/progress/recap").then(json<SessionRecap | null>),
  getPronunciationTrend: (): Promise<PronunciationTrendPoint[]> =>
    fetch("/progress/pronunciation").then(json<PronunciationTrendPoint[]>),
  explainFlag: (flagId: string): Promise<Explanation> => fetch(`/review/flags/${flagId}/explain`).then(json<Explanation>),
  submitPractice: (flagId: string, attemptText: string, roleplaySlug?: string): Promise<PracticeAttempt> =>
    fetch(`/review/flags/${flagId}/practice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attempt_text: attemptText, roleplay_slug: roleplaySlug }),
    }).then(json<PracticeAttempt>),

  // Multipart: no Content-Type header -- the browser must set it itself so the
  // boundary is included.
  assessPronunciation: (wav: Blob, referenceText: string): Promise<PronunciationResult> => {
    const form = new FormData();
    form.append("audio", wav, "attempt.wav");
    form.append("reference_text", referenceText);
    return fetch("/pronunciation/assess", { method: "POST", body: form }).then(json<PronunciationResult>);
  },

  // Raw WAV bytes, not JSON -- can't go through json<T>() above, which
  // assumes a JSON body on both success and error paths.
  synthesizeSpeech: async (text: string): Promise<Blob> => {
    const res = await fetch("/tts/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const message = (body as { error?: string }).error ?? `Request failed: ${res.status}`;
      throw createApiClientError(message, res.status);
    }
    return res.blob();
  },
};
