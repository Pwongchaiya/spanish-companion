import type {
  DictationExercise,
  DictationResult,
  Explanation,
  Flag,
  FlagStatus,
  MistakePatternSummary,
  Persona,
  PracticeAttempt,
  PronunciationResult,
  PronunciationTrendPoint,
  SessionRecap,
  SessionReplay,
  SessionScenario,
  SessionStatus,
  SpeakingTotal,
  TaskOutcome,
  TopicCoverageEntry,
  Transcription,
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
  startSession: (
    scenarioText?: string,
    sessionLengthHint?: string,
    pressureLevel?: string,
    variant?: string,
    scenarioSlug?: string,
    persona?: string,
  ): Promise<SessionStatus> =>
    fetch("/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_text: scenarioText,
        session_length_hint: sessionLengthHint,
        pressure_level: pressureLevel,
        variant,
        scenario_slug: scenarioSlug,
        persona,
      }),
    }).then(json<SessionStatus>),
  listPersonas: (): Promise<Persona[]> => fetch("/personas").then(json<Persona[]>),
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
  getTaskOutcome: (): Promise<TaskOutcome | null> => fetch("/review/task-outcome").then(json<TaskOutcome | null>),
  explainFlag: (flagId: string): Promise<Explanation> => fetch(`/review/flags/${flagId}/explain`).then(json<Explanation>),
  submitPractice: (flagId: string, attemptText: string, roleplaySlug?: string): Promise<PracticeAttempt> =>
    fetch(`/review/flags/${flagId}/practice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attempt_text: attemptText, roleplay_slug: roleplaySlug }),
    }).then(json<PracticeAttempt>),
  getDictationExercise: (excludeFlagId?: string): Promise<DictationExercise> =>
    fetch(`/review/dictation${excludeFlagId ? `?exclude=${encodeURIComponent(excludeFlagId)}` : ""}`).then(
      json<DictationExercise>,
    ),
  // E3: newest recorded session's replay. 404 from /latest (nothing recorded, or
  // recording is off) -> null, not an error.
  getLatestReplay: async (): Promise<SessionReplay | null> => {
    const latest = await fetch("/review/sessions/latest");
    if (latest.status === 404) return null;
    const { session_log_id } = await json<{ session_log_id: number }>(latest);
    return fetch(`/review/sessions/${session_log_id}/replay`).then(json<SessionReplay>);
  },
  checkDictation: (flagId: string, typedText: string): Promise<DictationResult> =>
    fetch(`/review/dictation/${flagId}/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ typed_text: typedText }),
    }).then(json<DictationResult>),

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
  // 204 (no completed session yet) -> null.
  getRecapSpeech: async (): Promise<Blob | null> => {
    const res = await fetch("/progress/recap/speech");
    if (res.status === 204) return null;
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const message = (body as { error?: string }).error ?? `Request failed: ${res.status}`;
      throw createApiClientError(message, res.status);
    }
    return res.blob();
  },

  // Multipart: no Content-Type header, same reasoning as assessPronunciation.
  transcribe: (wav: Blob): Promise<Transcription> => {
    const form = new FormData();
    form.append("audio", wav, "attempt.wav");
    return fetch("/transcribe", { method: "POST", body: form }).then(json<Transcription>);
  },

  updateFlagStatus: (flagId: string, status: FlagStatus): Promise<Flag> =>
    fetch(`/review/flags/${flagId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }).then(json<Flag>),

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
