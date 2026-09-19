import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type {
  MistakePatternSummary,
  PronunciationTrendPoint,
  SpeakingTotal,
  TopicCoverageEntry,
  UnflaggedStreak,
} from "../api/types";
import { runWithBackoff } from "./useBackoffRetry";

export function useProgress() {
  const [mistakes, setMistakes] = useState<MistakePatternSummary[]>([]);
  const [topics, setTopics] = useState<TopicCoverageEntry[]>([]);
  const [speaking, setSpeaking] = useState<SpeakingTotal | null>(null);
  const [streak, setStreak] = useState<UnflaggedStreak | null>(null);
  const [trend, setTrend] = useState<PronunciationTrendPoint[]>([]);
  const [trendLoaded, setTrendLoaded] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);

  useEffect(() => {
    const cancelMistakes = runWithBackoff(
      () => apiClient.listMistakeSummary(),
      setMistakes,
      "Having trouble reaching the server.",
      "Your mistake summary will show up once it's back.",
    );
    const cancelTopics = runWithBackoff(
      () => apiClient.listTopicCoverage(),
      (result) => {
        setTopics(result);
        setHasLoaded(true);
      },
      "Having trouble reaching the server.",
      "The coverage map will show up once it's back.",
    );
    // C1/C3 stay out of hasLoaded on purpose: it gates the mistakes/topics
    // empty-state copy, and a slow session_log read shouldn't hold that
    // back. Their own tiles render from null until they arrive.
    const cancelSpeaking = runWithBackoff(
      () => apiClient.getSpeakingTotal(),
      setSpeaking,
      "Having trouble reaching the server.",
      "Your speaking total will show up once it's back.",
    );
    const cancelStreak = runWithBackoff(
      () => apiClient.getUnflaggedStreak(),
      setStreak,
      "Having trouble reaching the server.",
      "Your clean-session streak will show up once it's back.",
    );
    // Own loaded flag, same reasoning as C1/C3 above: the trend read must not
    // gate the mistakes/topics copy, and its empty state must not flash early.
    const cancelTrend = runWithBackoff(
      () => apiClient.getPronunciationTrend(),
      (result) => {
        setTrend(result);
        setTrendLoaded(true);
      },
      "Having trouble reaching the server.",
      "Your pronunciation trend will show up once it's back.",
    );
    return () => {
      cancelMistakes();
      cancelTopics();
      cancelSpeaking();
      cancelStreak();
      cancelTrend();
    };
  }, []);

  return { mistakes, topics, speaking, streak, trend, trendLoaded, hasLoaded };
}
