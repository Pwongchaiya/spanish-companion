import { useState } from "react";
import { apiClient } from "../api/client";
import type { ApiClientError } from "../api/client";
import type { DictationExercise, DictationResult } from "../api/types";

// Review-only, on demand (nothing fetched until start()). Errors stay local to
// the panel -- no toast/connection machinery, same shape as MinimalPairDrill.
export function useDictation() {
  const [exercise, setExercise] = useState<DictationExercise | null>(null);
  const [result, setResult] = useState<DictationResult | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function start() {
    const previous = exercise?.flag_id;
    setResult(null);
    setAudioUrl(null);
    setError(null);
    setLoading(true);
    try {
      setExercise(await apiClient.getDictationExercise(previous));
    } catch (e) {
      setExercise(null);
      setError(
        (e as ApiClientError).status === 404
          ? "No other flagged sentence to dictate yet."
          : "Couldn't load a sentence. Try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function listen() {
    if (!exercise) return;
    setError(null);
    try {
      const blob = await apiClient.synthesizeSpeech(exercise.target);
      setAudioUrl(URL.createObjectURL(blob));
    } catch {
      setError("Couldn't load the audio. Try again.");
    }
  }

  async function check(typedText: string) {
    if (!exercise) return;
    setError(null);
    try {
      setResult(await apiClient.checkDictation(exercise.flag_id, typedText));
    } catch {
      setError("Couldn't check that. Your text is still in the box.");
    }
  }

  return { exercise, result, audioUrl, error, loading, start, listen, check };
}
