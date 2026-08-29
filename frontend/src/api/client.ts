import type { Explanation, Flag, PracticeAttempt, SessionStatus } from "./types";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const apiClient = {
  getStatus: (): Promise<SessionStatus> => fetch("/status").then(json<SessionStatus>),
  startSession: (): Promise<SessionStatus> => fetch("/start", { method: "POST" }).then(json<SessionStatus>),
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
