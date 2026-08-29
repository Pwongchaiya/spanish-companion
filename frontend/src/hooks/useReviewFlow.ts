import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { Explanation, Flag, PracticeAttempt } from "../api/types";

export function useReviewFlow() {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [attempt, setAttempt] = useState<PracticeAttempt | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.listFlags().then(setFlags).catch((e) => setError(e.message));
  }, []);

  async function selectFlag(flagId: string) {
    setSelectedFlagId(flagId);
    setExplanation(null);
    setAttempt(null);
    setError(null);
    try {
      setExplanation(await apiClient.explainFlag(flagId));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function submitPractice(attemptText: string) {
    if (!selectedFlagId) return;
    try {
      setAttempt(await apiClient.submitPractice(selectedFlagId, attemptText));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const selectedFlag = flags.find((f) => f.id === selectedFlagId) ?? null;

  return { flags, selectedFlag, explanation, attempt, error, selectFlag, submitPractice };
}
