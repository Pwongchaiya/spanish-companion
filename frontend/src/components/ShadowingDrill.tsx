import { useState } from "react";
import { apiClient } from "../api/client";
import type { PronunciationResult } from "../api/types";
import { blobToWav16k } from "../audio/encodeWav";
import { pickRandomSentence } from "../data/shadowingSentences";
import { useRecorder } from "../hooks/useRecorder";
import { PronunciationHeatmap } from "./PronunciationHeatmap";
import "./ShadowingDrill.css";

// ponytail: local useState only, same call as MinimalPairDrill -- not wired
// into the toast/backoff machinery; a failed attempt is one retry click away.
export function ShadowingDrill() {
  const [sentence, setSentence] = useState(() => pickRandomSentence());
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PronunciationResult | null>(null);
  const recorder = useRecorder();

  function next() {
    setSentence(pickRandomSentence(sentence));
    setAudioUrl(null);
    setError(null);
    setResult(null);
  }

  async function playReference() {
    setPlaying(true);
    setError(null);
    try {
      const blob = await apiClient.synthesizeSpeech(sentence);
      setAudioUrl(URL.createObjectURL(blob));
    } catch {
      setError("Couldn't load the reference audio. Try again.");
    } finally {
      setPlaying(false);
    }
  }

  async function submit() {
    if (!recorder.blob) return;
    setSubmitting(true);
    setError(null);
    try {
      const wav = await blobToWav16k(recorder.blob);
      setResult(await apiClient.assessPronunciation(wav, sentence));
    } catch (err) {
      // json<T> puts the server's {"error"} text (400/413/500) on err.message.
      setError(err instanceof Error ? err.message : "Couldn't score that attempt. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const recording = recorder.status === "recording";
  const shownError = error ?? recorder.error;

  return (
    <div className="shadow">
      <p className="shadow-kicker">Listen, then repeat the sentence</p>
      <p className="shadow-sentence">{sentence}</p>

      <div className="shadow-actions">
        <button type="button" onClick={playReference} disabled={playing || recording}>
          {playing ? "Loading…" : "▶ Play"}
        </button>
        {recording ? (
          <button type="button" onClick={recorder.stop}>
            ■ Stop
          </button>
        ) : (
          <button type="button" onClick={recorder.start} disabled={submitting}>
            ● Record
          </button>
        )}
        <button type="button" onClick={submit} disabled={!recorder.blob || recording || submitting}>
          {submitting ? "Scoring…" : "Submit"}
        </button>
      </div>
      {audioUrl && <audio src={audioUrl} autoPlay data-testid="shadow-audio" />}
      {shownError && <p className="shadow-error">{shownError}</p>}

      {result && (
        <div className="shadow-result">
          <dl className="shadow-scores">
            <div>
              <dt>Overall</dt>
              <dd>{Math.round(result.overall)}</dd>
            </div>
            <div>
              <dt>Accuracy</dt>
              <dd>{Math.round(result.accuracy)}</dd>
            </div>
            <div>
              <dt>Fluency</dt>
              <dd>{Math.round(result.fluency)}</dd>
            </div>
            <div>
              <dt>Completeness</dt>
              <dd>{Math.round(result.completeness)}</dd>
            </div>
            {result.prosody !== null && (
              <div>
                <dt>Prosody</dt>
                <dd>{Math.round(result.prosody)}</dd>
              </div>
            )}
          </dl>
          <PronunciationHeatmap words={result.words} />
        </div>
      )}

      <button className="shadow-next" type="button" onClick={next}>
        Next sentence
      </button>
    </div>
  );
}
