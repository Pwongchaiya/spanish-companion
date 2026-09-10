import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { Explanation, Flag, PracticeAttempt } from "../api/types";
import { useToastStore } from "../state/toastStore";

export function useReviewFlow() {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [attempt, setAttempt] = useState<PracticeAttempt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    apiClient
      .listFlags()
      .then(setFlags)
      .catch((e) => {
        setError(e.message);
        addToast(`Couldn't load flagged errors: ${e.message}`);
      });
  }, [addToast]);

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
