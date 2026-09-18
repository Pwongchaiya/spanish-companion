import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { MistakePatternSummary, TopicCoverageEntry } from "../api/types";
import { runWithBackoff } from "./useBackoffRetry";

export function useProgress() {
  const [mistakes, setMistakes] = useState<MistakePatternSummary[]>([]);
  const [topics, setTopics] = useState<TopicCoverageEntry[]>([]);
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
    return () => {
      cancelMistakes();
      cancelTopics();
    };
  }, []);

  return { mistakes, topics, hasLoaded };
}
