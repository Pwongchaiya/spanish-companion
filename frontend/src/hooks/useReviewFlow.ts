import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import type { ApiClientError } from "../api/client";
import type { Explanation, Flag, PracticeAttempt } from "../api/types";
import { useToastStore } from "../state/toastStore";
import { useConnectionStore } from "../state/connectionStore";
import { classifyError } from "../api/errorClassification";
import { runWithBackoff } from "./useBackoffRetry";

export function useReviewFlow() {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [attempt, setAttempt] = useState<PracticeAttempt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    return runWithBackoff(() => apiClient.listFlags(), setFlags);
  }, []);

  function handleCaughtError(e: unknown, retry: () => void) {
    const treatment = classifyError(e as ApiClientError);
    if (treatment.kind === "field") {
      setError(treatment.message);
    } else if (treatment.kind === "toast") {
      addToast(treatment.message);
    } else {
      useConnectionStore.getState().setDown(
        "Having trouble reaching the server.",
        undefined,
        retry,
      );
    }
  }

  async function selectFlag(flagId: string) {
    setSelectedFlagId(flagId);
    setExplanation(null);
    setAttempt(null);
    setError(null);
    try {
      setExplanation(await apiClient.explainFlag(flagId));
    } catch (e) {
      handleCaughtError(e, () => selectFlag(flagId));
    }
  }

  async function submitPractice(attemptText: string) {
    if (!selectedFlagId) return;
    try {
      setAttempt(await apiClient.submitPractice(selectedFlagId, attemptText));
    } catch (e) {
      handleCaughtError(e, () => submitPractice(attemptText));
    }
  }

  function backToList() {
    setSelectedFlagId(null);
    setExplanation(null);
    setAttempt(null);
    setError(null);
  }

  const selectedFlag = flags.find((f) => f.id === selectedFlagId) ?? null;

  return { flags, selectedFlag, explanation, attempt, error, selectFlag, submitPractice, backToList };
}
