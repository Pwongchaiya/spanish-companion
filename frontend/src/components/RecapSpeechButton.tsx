import { useState } from "react";
import { apiClient } from "../api/client";

// E4 spoken recap: on-demand only (click), Review-side -- never autoplays.
// ponytail: local useState, same shape as MinimalPairDrill's play().
export function RecapSpeechButton() {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function play() {
    setLoading(true);
    setError(null);
    try {
      const blob = await apiClient.getRecapSpeech();
      if (blob) setAudioUrl(URL.createObjectURL(blob));
      else setError("No recap to read yet.");
    } catch {
      setError("Couldn't load the audio. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button type="button" onClick={play} disabled={loading}>
        {loading ? "Loading…" : "▶ Listen"}
      </button>
      {audioUrl && <audio src={audioUrl} autoPlay data-testid="recap-audio" />}
      {error && <p className="drill-error">{error}</p>}
    </>
  );
}
