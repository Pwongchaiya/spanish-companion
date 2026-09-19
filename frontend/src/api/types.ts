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
  source_excerpt: string;
}

export interface PracticeAttempt {
  flag_id: string;
  attempt_text: string;
  timestamp: string;
  mastered: boolean;
}

export type TurnState = "listening" | "thinking" | "speaking" | "idle" | null;

export interface SessionScenario {
  proficiency_level: string;
  focus_category: string | null;
  suggested_topic: string | null;
  recent_mistake_categories: string[];
}

export interface MistakePatternSummary {
  id: number;
  profile_id: number;
  category: string;
  occurrence_count: number;
  last_seen_at: string;
  status: "active" | "resolved";
}

export interface SpeakingTotal {
  total_seconds: number;
  session_count: number;
}

export interface UnflaggedStreak {
  longest: number;
  current: number;
}

export interface TopicCoverageEntry {
  topic: string;
  covered: boolean;
  first_covered_at: string | null;
}

export interface SessionRecap {
  flag_count: number;
  categories_flagged: string[];
  session_started_at: string;
  session_ended_at: string | null;
}

export type ServerEvent =
  | { type: "status"; status: SessionStatus }
  | { type: "transcript"; turns: TranscriptTurn[] }
  | { type: "flags"; flags: Flag[] }
  | { type: "turn_state"; state: TurnState };
