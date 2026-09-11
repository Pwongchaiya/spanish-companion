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
  // Distinguishes "the server said there's nothing flagged" from "we don't
  // know yet, because listFlags has never actually succeeded" -- flags.length
  // === 0 is true for both, and conflating them showed "Nothing was flagged
  // last time" for an outage that never loaded anything.
  const [hasLoaded, setHasLoaded] = useState(false);
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [attempt, setAttempt] = useState<PracticeAttempt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    return runWithBackoff(
      () => apiClient.listFlags(),
      (result) => {
        setFlags(result);
        setHasLoaded(true);
      },
      "Having trouble reaching the server.",
      "These are the flags from last time, held locally.",
    );
  }, []);

  function handleCaughtError(e: unknown, retry: () => void, friendlyMessage: string, friendlySubMessage: string) {
    const treatment = classifyError(e as ApiClientError);
    if (treatment.kind === "field") {
      setError(treatment.message);
    } else if (treatment.kind === "toast") {
      addToast(friendlyMessage, { subMessage: friendlySubMessage, retry });
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
      handleCaughtError(
        e,
        () => selectFlag(flagId),
        "Couldn't load that explanation.",
        "Try selecting the flag again.",
      );
    }
  }

  async function submitPractice(attemptText: string) {
    if (!selectedFlagId) return;
    try {
      setAttempt(await apiClient.submitPractice(selectedFlagId, attemptText));
    } catch (e) {
      handleCaughtError(
        e,
        () => submitPractice(attemptText),
        "Couldn't save that practice attempt.",
        "Your answer is still in the box.",
      );
    }
  }

  function backToList() {
    setSelectedFlagId(null);
    setExplanation(null);
    setAttempt(null);
    setError(null);
  }

  const selectedFlag = flags.find((f) => f.id === selectedFlagId) ?? null;

  return { flags, hasLoaded, selectedFlag, explanation, attempt, error, selectFlag, submitPractice, backToList };
}
