import { create } from "zustand";

export type ConnectionPhase = "ok" | "retrying" | "down";

interface ConnectionState {
  phase: ConnectionPhase;
  attempt: number;
  maxAttempts: number;
  message: string;
  subMessage?: string;
  retry: (() => void) | null;
  setRetrying: (attempt: number, maxAttempts: number) => void;
  setDown: (message: string, subMessage: string | undefined, retry: (() => void) | null) => void;
  setOk: () => void;
  /** SSE has no attempt count of its own (the browser retries internally) --
   * this only nudges phase to "retrying" if nothing else already owns it,
   * so it never clobbers an in-progress backoff sequence from a fetch. */
  noteTransientIssue: () => void;
}

// ponytail: single shared banner state for the whole app (one source of
// truth, per the Aliento error-handling mockup) -- not worth a Context
// provider when Zustand's global store already does this everywhere else.
export const useConnectionStore = create<ConnectionState>()((set, get) => ({
  phase: "ok",
  attempt: 0,
  maxAttempts: 0,
  message: "",
  subMessage: undefined,
  retry: null,
  setRetrying: (attempt, maxAttempts) => set({ phase: "retrying", attempt, maxAttempts }),
  setDown: (message, subMessage, retry) => set({ phase: "down", message, subMessage, retry }),
  setOk: () => set({ phase: "ok", attempt: 0, maxAttempts: 0, message: "", subMessage: undefined, retry: null }),
  noteTransientIssue: () => {
    if (get().phase === "ok") set({ phase: "retrying", attempt: 0, maxAttempts: 0 });
  },
}));
