import { useState } from "react";
import { useReviewFlow } from "../hooks/useReviewFlow";

export function ReviewView() {
  const { flags, selectedFlag, explanation, attempt, error, selectFlag, submitPractice } = useReviewFlow();
  const [attemptText, setAttemptText] = useState("");

  return (
    <div className="view">
      {error && <p className="conn-error">{error}</p>}

      {!selectedFlag && (
        <>
          <h2>Flagged errors</h2>
          {flags.length === 0 && <p className="empty">No flagged errors from the last session.</p>}
          <ul className="flag-list">
            {flags.map((flag) => (
              <li key={flag.id}>
                <button className="flag-item" onClick={() => selectFlag(flag.id)}>
                  <span className="said">{flag.said}</span>
                  <span className="arrow">→</span>
                  <span className="corrected">{flag.corrected}</span>
                  <span className="category">{flag.category}</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      {selectedFlag && (
        <div className="review-detail">
          <h2>
            <span className="said">{selectedFlag.said}</span> → <span className="corrected">{selectedFlag.corrected}</span>
          </h2>

          {!explanation && <p className="empty">Loading explanation…</p>}
          {explanation && (
            <div className="explanation">
              <p>{explanation.explanation}</p>
              <a href={explanation.source_url} target="_blank" rel="noreferrer">
                {explanation.source_url}
              </a>
            </div>
          )}

          {explanation && !attempt && (
            <form
              className="practice-form"
              onSubmit={(e) => {
                e.preventDefault();
                submitPractice(attemptText);
              }}
            >
              <label htmlFor="practice-input">Now try saying it correctly:</label>
              <input
                id="practice-input"
                value={attemptText}
                onChange={(e) => setAttemptText(e.target.value)}
                placeholder={selectedFlag.corrected}
                autoFocus
              />
              <button className="primary" type="submit" disabled={!attemptText.trim()}>
                Submit
              </button>
            </form>
          )}

          {attempt && <p className="done">Nice work — logged: "{attempt.attempt_text}"</p>}
        </div>
      )}
    </div>
  );
}
