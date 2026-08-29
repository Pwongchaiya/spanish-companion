export interface SessionStatus {
  running: boolean;
  ready: boolean;
  graceful: boolean | null;
}

export interface TranscriptTurn {
  role: "user" | "assistant";
  text: string;
}

export interface Flag {
  id: string;
  said: string;
  corrected: string;
  category: string;
  timestamp: string;
}

export interface Explanation {
  explanation: string;
  source_url: string;
}

export interface PracticeAttempt {
  flag_id: string;
  attempt_text: string;
  timestamp: string;
}

export type ServerEvent =
  | { type: "status"; status: SessionStatus }
  | { type: "transcript"; turns: TranscriptTurn[] }
  | { type: "flags"; flags: Flag[] };
