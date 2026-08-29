import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { Flag, ServerEvent, SessionStatus, TranscriptTurn } from "../api/types";

interface SessionStore {
  status: SessionStatus;
  transcript: TranscriptTurn[];
  flags: Flag[];
  setStatus: (status: SessionStatus) => void;
  applyEvent: (event: ServerEvent) => void;
}

const INITIAL_STATUS: SessionStatus = { running: false, ready: false, graceful: null };

export const useSessionStore = create<SessionStore>()(
  devtools((set) => ({
    status: INITIAL_STATUS,
    transcript: [],
    flags: [],
    setStatus: (status) => set({ status }, false, "setStatus"),
    applyEvent: (event) =>
      set(
        () => {
          switch (event.type) {
            case "status":
              return { status: event.status };
            case "transcript":
              return { transcript: event.turns };
            case "flags":
              return { flags: event.flags };
          }
        },
        false,
        `applyEvent/${event.type}`,
      ),
  })),
);
