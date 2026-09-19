import { useState } from "react";
import { useDictation } from "../hooks/useDictation";
import "./DictationPanel.css";

// Phase 5 E2: type back a sentence from your own flags. Orthography (accent /
// spelling) differences are legitimate here -- it is the one typed surface.
export function DictationPanel() {
  const { exercise, result, audioUrl, error, loading, start, listen, check } = useDictation();
  const [typed, setTyped] = useState("");

  function begin() {
    setTyped("");
    start();
  }

  if (!exercise) {
    return (
      <div className="dictation">
        <button type="button" onClick={begin} disabled={loading}>
          {loading ? "Loading…" : "Dictation: type a sentence back"}
        </button>
        {error && <p className="dictation-error">{error}</p>}
      </div>
    );
  }

  return (
    <div className="dictation">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          check(typed);
        }}
      >
        <label htmlFor="dictation-input">Listen, then type the sentence.</label>
        <button type="button" onClick={listen}>
          ▶ Listen
        </button>
        {audioUrl && <audio src={audioUrl} autoPlay data-testid="dictation-audio" />}
        <input
          id="dictation-input"
          type="text"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          autoComplete="off"
          spellCheck={false}
        />
        <button type="submit" disabled={!typed.trim()}>
          Check
        </button>
      </form>
      {error && <p className="dictation-error">{error}</p>}
      {result && (
        <div className="dictation-result" data-testid="dictation-result">
          <p>{result.matches ? "Exact match." : "Not quite:"}</p>
          <p className="dictation-words">
            {result.words.map((w, i) => (
              <span key={i} className={`dw dw-${w.status}`} data-status={w.status}>
                {w.status === "ok" ? w.target : w.target || "(extra)"}
                {w.status !== "ok" && w.typed && ` (you typed ${w.typed})`}
                {w.status === "accent" && " accent"}
              </span>
            ))}
          </p>
          <button type="button" onClick={begin}>
            Another
          </button>
        </div>
      )}
    </div>
  );
}
