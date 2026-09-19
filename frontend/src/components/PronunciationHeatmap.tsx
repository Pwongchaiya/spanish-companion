import { useState } from "react";
import type { WordScore } from "../api/types";
import "./PronunciationHeatmap.css";

// ponytail: presentational only; expanded-word state is local. Bands per the
// Azure accuracy convention: >=80 good, 60-79 warn, <60 poor.
export function band(accuracy: number | null): "good" | "warn" | "poor" | "none" {
  if (accuracy === null) return "none";
  return accuracy >= 80 ? "good" : accuracy >= 60 ? "warn" : "poor";
}

function label(w: WordScore): string {
  const score = w.accuracy === null ? "no score" : `${Math.round(w.accuracy)}`;
  return w.error_type !== "None" ? `${w.word}, ${score}, ${w.error_type}` : `${w.word}, ${score}`;
}

export function PronunciationHeatmap({ words }: { words: WordScore[] }) {
  const [open, setOpen] = useState<number | null>(null);
  const expanded = open === null ? null : words[open];

  return (
    <div className="heatmap">
      <div className="heatmap-words">
        {words.map((w, i) => (
          <button
            key={i}
            type="button"
            className={`heatmap-word ${band(w.accuracy)}${w.error_type !== "None" ? " has-error" : ""}`}
            aria-label={label(w)}
            aria-expanded={open === i}
            onClick={() => setOpen(open === i ? null : i)}
          >
            <span className="heatmap-text">{w.word}</span>
            <span className="heatmap-score">{w.accuracy === null ? "–" : Math.round(w.accuracy)}</span>
            {w.error_type !== "None" && <span className="heatmap-error">{w.error_type}</span>}
          </button>
        ))}
      </div>

      {expanded && (
        <ul className="heatmap-phonemes" aria-label={`Phonemes for ${expanded.word}`}>
          {expanded.phonemes.length === 0 ? (
            <li className="heatmap-empty">No phoneme detail</li>
          ) : (
            expanded.phonemes.map((p, j) => (
              <li key={j} className={`heatmap-chip ${band(p.accuracy)}`}>
                {p.phoneme} <span className="heatmap-score">{Math.round(p.accuracy)}</span>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
