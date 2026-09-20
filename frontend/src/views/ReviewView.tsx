import { useState } from "react";
import { useReviewFlow } from "../hooks/useReviewFlow";
import { useConnectionStore } from "../state/connectionStore";
import { DictationPanel } from "../components/DictationPanel";
import { ReplayPanel } from "../components/ReplayPanel";
import { groupScenariosByTier } from "../data/roleplayScenarios";
import "./ReviewView.css";

export function ReviewView() {
  const {
    flags,
    hasLoaded,
    selectedFlag,
    explanation,
    attempt,
    error,
    taskOutcome,
    selectFlag,
    submitPractice,
    backToList,
  } = useReviewFlow();
  const [attemptText, setAttemptText] = useState("");
  const [roleplaySlug, setRoleplaySlug] = useState("");
  // Explaining a flag needs retrieval, and retrieval needs the server -- so
  // the list stays visible but non-interactive during an outage rather than
  // failing silently per-click (Aliento error-handling mockup, "Review gets
  // the identical band").
  const connectionOk = useConnectionStore((s) => s.phase === "ok");
  // "Nothing was flagged" and "you can read the list" both claim a real,
  // previously-loaded list -- neither is true if listFlags has never
  // actually succeeded (e.g. the backend was already down on first visit).
  const hasCachedList = hasLoaded && flags.length > 0;

  return (
    <div className="view">
      {!selectedFlag && (
        <>
          <div className="live">
            <div className="ring">
              <i />
            </div>
            <div className="st">Flagged</div>
            {taskOutcome && (
              <p className={`task-badge task-${taskOutcome.outcome ?? "pending"}`} title={taskOutcome.success_condition}>
                {taskOutcome.label}:{" "}
                {taskOutcome.outcome === "success"
                  ? "Task complete"
                  : taskOutcome.outcome === "fail"
                    ? "Task not completed"
                    : "Not judged yet"}
              </p>
            )}
            {!connectionOk && hasCachedList && (
              <p className="hint">You can read the list. Explanations come from the server, so those wait.</p>
            )}
          </div>

          {!hasLoaded && !connectionOk && <p className="empty">Can&rsquo;t check for flags right now.</p>}
          {hasLoaded && flags.length === 0 && (
            <p className="empty">Nothing was flagged last time. That happens.</p>
          )}
          {flags.length > 0 && (
            <div className="flags">
              {flags.map((flag) => (
                <button
                  key={flag.id}
                  className="flag"
                  type="button"
                  disabled={!connectionOk}
                  onClick={() => selectFlag(flag.id)}
                >
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
          {connectionOk && flags.length > 0 && <DictationPanel />}
          {connectionOk && <ReplayPanel />}
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
                {explanation.source_excerpt && <blockquote className="excerpt">{explanation.source_excerpt}</blockquote>}
              </div>
            </div>
          )}

          {explanation && (
            <form
              className="practice"
              onSubmit={(e) => {
                e.preventDefault();
                submitPractice(attemptText, roleplaySlug || undefined);
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
              <label htmlFor="practice-roleplay">Practice it in a scene (optional)</label>
              <select
                id="practice-roleplay"
                value={roleplaySlug}
                onChange={(e) => setRoleplaySlug(e.target.value)}
              >
                <option value="">Just the sentence</option>
                {groupScenariosByTier().map((g) => (
                  <optgroup key={g.tier} label={g.label}>
                    {g.scenarios.map((s) => (
                      <option key={s.slug} value={s.slug}>
                        {s.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
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
            <div className="st">
              <span>{attempt.mastered ? "Mastered" : "Logged"}</span>{" "}
              <span className="grade">({attempt.grade})</span>
            </div>
          </div>

          <div>
            <p className="kicker">{selectedFlag.category}</p>
            <p className="logged">
              You said it back as <q>{attempt.attempt_text}</q> — that&rsquo;s the one.{" "}
              {attempt.mastered
                ? "You've got this one now."
                : "It's saved with the flag — you'll see it again."}
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
