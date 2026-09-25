import { useEffect, useRef, useState } from "react";
import { apiClient } from "../api/client";
import type { ApiClientError } from "../api/client";
import { blobToWav16k } from "../audio/encodeWav";
import type {
  Explanation,
  Flag,
  FlagStatus,
  MistakePatternSummary,
  PracticeAttempt,
  SessionRecap,
  TaskOutcome,
} from "../api/types";
import { useToastStore } from "../state/toastStore";
import { useConnectionStore } from "../state/connectionStore";
import { classifyError } from "../api/errorClassification";
import { runWithBackoff } from "./useBackoffRetry";

export type PracticePhase = "idle" | "listening" | "scoring" | "denied" | "nospeech" | "typed";

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
  const [taskOutcome, setTaskOutcome] = useState<TaskOutcome | null>(null);
  const [sessionRecap, setSessionRecap] = useState<SessionRecap | null>(null);
  const [replayDurationSeconds, setReplayDurationSeconds] = useState<number | null>(null);
  const [mistakeSummary, setMistakeSummary] = useState<MistakePatternSummary[]>([]);
  const [practicePhase, setPracticePhaseState] = useState<PracticePhase>("idle");
  // Set from the transcribe response, consumed immediately by the nospeech
  // notice ("0 words · 3.1s of audio") -- not carried across flags/attempts.
  const [lastRecordedSeconds, setLastRecordedSeconds] = useState<number | null>(null);
  const addToast = useToastStore((s) => s.addToast);

  // ponytail: bumped on every user-driven phase change (not the internal
  // "scoring" one submitSpokenPractice sets on itself) so a transcribe/grade
  // response that resolves after the user cancelled or moved on gets
  // dropped instead of jumping the UI out from under them.
  const practiceTokenRef = useRef(0);
  function setPracticePhase(next: PracticePhase) {
    if (next !== "scoring") practiceTokenRef.current += 1;
    setPracticePhaseState(next);
  }

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

  // Best-effort, never toasts -- each of these is a nicety (badge, duration,
  // repeat tag), not core to the review flow.
  useEffect(() => {
    let cancelled = false;
    apiClient
      .getTaskOutcome()
      .then((result) => {
        if (!cancelled) setTaskOutcome(result);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getSessionRecap()
      .then((result) => {
        if (!cancelled) setSessionRecap(result);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .getLatestReplay()
      .then((result) => {
        if (!cancelled && result) setReplayDurationSeconds(result.duration_seconds);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .listMistakeSummary()
      .then((result) => {
        if (!cancelled) setMistakeSummary(result);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // Auto-select the first flag once loaded: the three-pane layout always has
  // a detail pane on screen, so it needs something to show rather than
  // waiting for a click (mirrors the design's default sel=0).
  useEffect(() => {
    if (hasLoaded && flags.length > 0 && !selectedFlagId) void selectFlag(flags[0].id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasLoaded, flags, selectedFlagId]);

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
    setPracticePhase("idle");
    // Offline: still show the flag itself (said/corrected are already in
    // hand), just skip the explain call -- it would only fail.
    if (useConnectionStore.getState().phase !== "ok") return;
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

  async function submitPractice(attemptText: string, roleplaySlug?: string) {
    if (!selectedFlagId) return;
    try {
      setAttempt(await apiClient.submitPractice(selectedFlagId, attemptText, roleplaySlug));
    } catch (e) {
      handleCaughtError(
        e,
        () => submitPractice(attemptText, roleplaySlug),
        "Couldn't save that practice attempt.",
        "Your answer is still in the box.",
      );
    }
  }

  // scoring -> blobToWav16k -> transcribe -> empty trim -> nospeech (no
  // attempt logged) -> else the existing text submitPractice.
  async function submitSpokenPractice(blob: Blob, roleplaySlug?: string) {
    setPracticePhaseState("scoring");
    const token = practiceTokenRef.current;
    try {
      const wav = await blobToWav16k(blob);
      const { text, duration_seconds } = await apiClient.transcribe(wav);
      if (practiceTokenRef.current !== token) return; // cancelled/moved on meanwhile
      setLastRecordedSeconds(duration_seconds);
      if (!text.trim()) {
        setPracticePhaseState("nospeech");
        return;
      }
      await submitPractice(text, roleplaySlug);
    } catch (e) {
      if (practiceTokenRef.current !== token) return;
      setPracticePhaseState("idle");
      handleCaughtError(
        e,
        () => submitSpokenPractice(blob, roleplaySlug),
        "Couldn't transcribe that attempt.",
        "Record again or type it instead.",
      );
    }
  }

  async function updateFlagStatus(flagId: string, status: FlagStatus) {
    const target = flags.find((f) => f.id === flagId);
    if (!target) return;
    // Pressing the same status again clears it back to open (matches the
    // design's m/s toggle behaviour).
    const nextStatus: FlagStatus = (target.status ?? "open") === status ? "open" : status;
    const prevFlags = flags;
    setFlags((fs) => fs.map((f) => (f.id === flagId ? { ...f, status: nextStatus } : f)));
    try {
      const updated = await apiClient.updateFlagStatus(flagId, nextStatus);
      setFlags((fs) => fs.map((f) => (f.id === flagId ? updated : f)));
    } catch (e) {
      setFlags(prevFlags);
      handleCaughtError(e, () => updateFlagStatus(flagId, status), "Couldn't update that flag.", "Try again.");
    }
  }

  const selectedFlag = flags.find((f) => f.id === selectedFlagId) ?? null;

  return {
    flags,
    hasLoaded,
    selectedFlag,
    explanation,
    attempt,
    error,
    taskOutcome,
    sessionRecap,
    replayDurationSeconds,
    mistakeSummary,
    practicePhase,
    lastRecordedSeconds,
    setPracticePhase,
    selectFlag,
    submitPractice,
    submitSpokenPractice,
    updateFlagStatus,
  };
}
