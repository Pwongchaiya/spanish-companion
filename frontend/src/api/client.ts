import type { Explanation, Flag, PracticeAttempt, SessionScenario, SessionStatus } from "./types";

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
  startSession: (scenarioText?: string, sessionLengthHint?: string): Promise<SessionStatus> =>
    fetch("/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_text: scenarioText, session_length_hint: sessionLengthHint }),
    }).then(json<SessionStatus>),
  stopSession: (): Promise<SessionStatus> => fetch("/stop", { method: "POST" }).then(json<SessionStatus>),

  listFlags: (): Promise<Flag[]> => fetch("/review/flags").then(json<Flag[]>),
  explainFlag: (flagId: string): Promise<Explanation> => fetch(`/review/flags/${flagId}/explain`).then(json<Explanation>),
  submitPractice: (flagId: string, attemptText: string): Promise<PracticeAttempt> =>
    fetch(`/review/flags/${flagId}/practice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ attempt_text: attemptText }),
    }).then(json<PracticeAttempt>),
};
