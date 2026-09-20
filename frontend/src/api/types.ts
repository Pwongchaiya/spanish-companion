export interface SessionStatus {
  running: boolean;
  ready: boolean;
  graceful: boolean | null;
}

export interface Persona {
  slug: string;
  name: string;
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

export interface DictationExercise {
  flag_id: string;
  target: string;
}

export type DictationWordStatus = "ok" | "accent" | "spelling" | "missing" | "extra";

export interface DictationWord {
  target: string;
  typed: string;
  status: DictationWordStatus;
}

export interface DictationResult {
  flag_id: string;
  target: string;
  typed_text: string;
  matches: boolean;
  words: DictationWord[];
}

export type PracticeGrade = "again" | "hard" | "good" | "easy";

export interface PracticeAttempt {
  flag_id: string;
  attempt_text: string;
  timestamp: string;
  mastered: boolean;
  grade: PracticeGrade;
}

// D4 task scenario result for the latest completed session; outcome null =
// not judged yet (no transcript, or the judge couldn't decide).
export interface TaskOutcome {
  scenario_slug: string;
  label: string;
  success_condition: string;
  outcome: "success" | "fail" | null;
}

export type TurnState = "listening" | "thinking" | "speaking" | "idle" | null;

export interface DuePattern {
  category: string;
  occurrence_count: number;
  days_overdue: number;
}

export interface SessionScenario {
  proficiency_level: string;
  focus_category: string | null;
  suggested_topic: string | null;
  recent_mistake_categories: string[];
  due_patterns?: DuePattern[];
  boss_fight_text?: string | null;
  boss_fight_categories?: string[];
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

export interface PhonemeScore {
  phoneme: string;
  accuracy: number;
}

export interface WordScore {
  word: string;
  accuracy: number | null;
  error_type: string; // 'None' | 'Omission' | 'Insertion' | 'Mispronunciation'
  phonemes: PhonemeScore[];
}

export interface PronunciationResult {
  reference_text: string;
  accuracy: number;
  fluency: number;
  completeness: number;
  prosody: number | null;
  overall: number;
  words: WordScore[];
  created_at: string;
}

export interface PronunciationTrendPoint {
  created_at: string;
  accuracy: number;
  fluency: number;
  overall: number;
}

export type ServerEvent =
  | { type: "status"; status: SessionStatus }
  | { type: "transcript"; turns: TranscriptTurn[] }
  | { type: "flags"; flags: Flag[] }
  | { type: "turn_state"; state: TurnState };
