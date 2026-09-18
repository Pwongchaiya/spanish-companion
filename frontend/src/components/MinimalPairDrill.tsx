import { useState } from "react";
import { apiClient } from "../api/client";
import { MINIMAL_PAIRS, pickRandomPair, pickRandomWord } from "../data/minimalPairs";
import "./MinimalPairDrill.css";

// ponytail: local useState only, no dedicated hook/store -- this is a
// Phase-1 "cheap win" drill (roadmap B6), not wired into the
// toast/connection/backoff-retry machinery ReviewView/useReviewFlow use.
// Promote to a hook if this grows a second consumer.
type Result = "correct" | "incorrect" | null;

export function MinimalPairDrill() {
  const [pair, setPair] = useState(() => pickRandomPair());
  const [playedWord, setPlayedWord] = useState(() => pickRandomWord(pair));
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result>(null);

  function newRound() {
    const nextPair = pickRandomPair(MINIMAL_PAIRS);
    setPair(nextPair);
    setPlayedWord(pickRandomWord(nextPair));
    setAudioUrl(null);
    setError(null);
    setResult(null);
  }

  async function play() {
    setLoading(true);
    setError(null);
    try {
      const blob = await apiClient.synthesizeSpeech(playedWord);
      setAudioUrl(URL.createObjectURL(blob));
    } catch {
      setError("Couldn't load the audio. Try again.");
    } finally {
      setLoading(false);
    }
  }

  function choose(word: string) {
    if (result) return;
    setResult(word === playedWord ? "correct" : "incorrect");
  }

  return (
    <div className="drill">
      <p className="drill-kicker">Listen and pick the word you heard</p>

      <button className="drill-play" type="button" onClick={play} disabled={loading}>
        {loading ? "Loading…" : "▶ Play"}
      </button>
      {audioUrl && <audio src={audioUrl} autoPlay data-testid="drill-audio" />}
      {error && <p className="drill-error">{error}</p>}

      <div className="drill-options">
        {[pair.a, pair.b].map((word) => (
          <button
            key={word}
            type="button"
            className={
              "drill-option" +
              (result && word === playedWord ? " correct" : "") +
              (result === "incorrect" && word !== playedWord ? " wrong-pick" : "")
            }
            onClick={() => choose(word)}
            disabled={!!result}
          >
            {word}
          </button>
        ))}
      </div>

      {result === "correct" && <p className="drill-feedback correct">Correct — that was {playedWord}.</p>}
      {result === "incorrect" && <p className="drill-feedback incorrect">Not quite — that was {playedWord}.</p>}

      {result && (
        <button className="drill-next" type="button" onClick={newRound}>
          Next pair
        </button>
      )}
    </div>
  );
}
