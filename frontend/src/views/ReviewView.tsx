import { useState } from "react";
import { useReviewFlow } from "../hooks/useReviewFlow";
import "./ReviewView.css";

export function ReviewView() {
  const { flags, selectedFlag, explanation, attempt, error, selectFlag, submitPractice, backToList } =
    useReviewFlow();
  const [attemptText, setAttemptText] = useState("");

  return (
    <div className="view">
      {!selectedFlag && (
        <>
          <div className="live">
            <div className="ring">
              <i />
            </div>
            <div className="st">Flagged</div>
          </div>

          {flags.length === 0 ? (
            <p className="empty">Nothing was flagged last time. That happens.</p>
          ) : (
            <div className="flags">
              {flags.map((flag) => (
                <button key={flag.id} className="flag" type="button" onClick={() => selectFlag(flag.id)}>
                  <span className="pair">
                    <span className="was">{flag.said}</span>
                    <span className="to">becomes</span>
                    <span className="now">{flag.corrected}</span>
                  </span>
                  <span className="cat">{flag.category}</span>
                </button>
              ))}
            </div>
          )}
        </>
      )}

      {selectedFlag && !attempt && (
        <>
          <div>
            <p className="kicker">{selectedFlag.category}</p>
            <h1 className="pair-hd">
              <span className="was">{selectedFlag.said}</span>
              <span className="to">becomes</span>
              <span className="now">{selectedFlag.corrected}</span>
            </h1>
          </div>

          {error && <p className="conn-error">{error}</p>}

          {!explanation && <p className="looking">Looking it up…</p>}

          {explanation && (
            <div className="explain">
              <p>{explanation.explanation}</p>
              <div className="source">
                <span className="lbl">Source:</span>
                <a href={explanation.source_url} target="_blank" rel="noreferrer">
                  {explanation.source_url}
                </a>
              </div>
            </div>
          )}

          {explanation && (
            <form
              className="practice"
              onSubmit={(e) => {
                e.preventDefault();
                submitPractice(attemptText);
              }}
            >
              <label htmlFor="practice-input">Now say it the way you meant it.</label>
              <input
                id="practice-input"
                type="text"
                value={attemptText}
                onChange={(e) => setAttemptText(e.target.value)}
                placeholder={selectedFlag.corrected}
                autoComplete="off"
                spellCheck={false}
                autoFocus
              />
              <button className="primary" type="submit" disabled={!attemptText.trim()}>
                Log this
              </button>
            </form>
          )}
        </>
      )}

      {selectedFlag && attempt && (
        <>
          <div className="live">
            <div className="ring closed">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path
                  d="M4.5 10.4 8.2 14 15.5 6.4"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <div className="st">Logged</div>
          </div>

          <div>
            <p className="kicker">{selectedFlag.category}</p>
            <p className="logged">
              You said it back as <q>{attempt.attempt_text}</q> — that&rsquo;s the one. It&rsquo;s saved with the flag.
            </p>
          </div>

          <button className="back-link" type="button" onClick={backToList}>
            Back to all flags
          </button>
        </>
      )}
    </div>
  );
}
