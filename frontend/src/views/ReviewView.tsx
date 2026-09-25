import { useEffect, useMemo, useRef, useState } from "react";
import { apiClient } from "../api/client";
import { useReviewFlow } from "../hooks/useReviewFlow";
import { useConnectionStore } from "../state/connectionStore";
import { DictationPanel } from "../components/DictationPanel";
import { ReplayPanel } from "../components/ReplayPanel";
import { groupScenariosByTier } from "../data/roleplayScenarios";
import { MAX_RECORD_MS, useRecorder } from "../hooks/useRecorder";
import type { Flag } from "../api/types";
import "./ReviewView.css";

type Pane = "rail" | "list" | "detail";
type ActivePanel = null | "dictation" | "replay";

const clock = (ms: number) => `${Math.floor(ms / 60000)}:${String(Math.floor(ms / 1000) % 60).padStart(2, "0")}`;
const MAX_CLOCK = clock(MAX_RECORD_MS);

// Flag.timestamp is wall-clock ISO -- rendered as local clock time (session-
// relative offsets only exist on ReplayFlag, a different shape).
function formatClockTime(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

function BackIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M12.5 4 6.5 10l6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="spin" width="18" height="18" viewBox="0 0 34 34" fill="none" aria-hidden="true">
      <circle cx="17" cy="17" r="14" stroke="var(--border)" strokeWidth="2.5" />
      <path d="M31 17A14 14 0 0 0 17 3" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

export function ReviewView() {
  const {
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
    attemptHeardSeconds,
    setPracticePhase,
    selectFlag,
    submitPractice,
    submitSpokenPractice,
    updateFlagStatus,
  } = useReviewFlow();

  const connectionOk = useConnectionStore((s) => s.phase === "ok");
  // "Nothing was flagged" and "you can read the list" both claim a real,
  // previously-loaded list -- neither is true if listFlags has never
  // actually succeeded (e.g. the backend was already down on first visit).
  const hasCachedList = hasLoaded && flags.length > 0;

  const [category, setCategory] = useState("All");
  const [pane, setPane] = useState<Pane>("list");
  const [activePanel, setActivePanel] = useState<ActivePanel>(null);
  const [attemptText, setAttemptText] = useState("");
  const [roleplaySlug, setRoleplaySlug] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [heardUrl, setHeardUrl] = useState<string | null>(null);
  const [liveMsg, setLiveMsg] = useState("");

  const recorder = useRecorder();
  const handledBlobRef = useRef<Blob | null>(null);
  const rowRefs = useRef(new Map<string, HTMLButtonElement>());

  const categoryList = useMemo(() => {
    const names: string[] = [];
    flags.forEach((f) => {
      if (!names.includes(f.category)) names.push(f.category);
    });
    return [{ name: "All", n: flags.length }, ...names.map((n) => ({ name: n, n: flags.filter((f) => f.category === n).length }))];
  }, [flags]);

  const visibleFlags = useMemo(
    () => (category === "All" ? flags : flags.filter((f) => f.category === category)),
    [flags, category],
  );

  const occurrenceByCategory = useMemo(() => {
    const map = new Map<string, number>();
    mistakeSummary.forEach((m) => map.set(m.category, m.occurrence_count));
    return map;
  }, [mistakeSummary]);

  const repeatCategoryCount = useMemo(() => {
    const seen = new Set<string>();
    flags.forEach((f) => {
      if ((occurrenceByCategory.get(f.category) ?? 0) > 1) seen.add(f.category);
    });
    return seen.size;
  }, [flags, occurrenceByCategory]);

  const sessionMinutes =
    sessionRecap?.session_ended_at != null
      ? Math.max(
          1,
          Math.round(
            (new Date(sessionRecap.session_ended_at).getTime() - new Date(sessionRecap.session_started_at).getTime()) /
              60000,
          ),
        )
      : null;

  // Scroll the selected row into view for keyboard (j/k) navigation.
  useEffect(() => {
    if (!selectedFlag) return;
    rowRefs.current.get(selectedFlag.id)?.scrollIntoView?.({ block: "nearest" });
  }, [selectedFlag]);

  useEffect(() => {
    const messages: Record<typeof practicePhase, string> = {
      idle: "Ready to record.",
      listening: "Listening. Tap to stop.",
      scoring: "Transcribing your answer, then grading it.",
      denied: "Microphone blocked. Type your answer instead, or allow the mic and try again.",
      nospeech: "No words were recognised. Record again or type it instead.",
      typed: "Typing your answer instead.",
    };
    setLiveMsg(messages[practicePhase]);
  }, [practicePhase]);

  useEffect(() => {
    if (recorder.status !== "recording") return;
    const t0 = Date.now();
    setElapsed(0);
    const id = setInterval(() => setElapsed(Date.now() - t0), 250);
    return () => clearInterval(id);
  }, [recorder.status]);

  // getUserMedia rejected (permission denied, no device, etc.) while we were
  // waiting on it -- only relevant if we were actually trying to listen.
  useEffect(() => {
    if (recorder.status === "error" && practicePhase === "listening") {
      setPracticePhase("denied");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.status]);

  // A finished recording is handed off for scoring exactly once.
  useEffect(() => {
    const blob = recorder.blob;
    if (recorder.status !== "done" || !blob || blob === handledBlobRef.current) return;
    handledBlobRef.current = blob;
    void submitSpokenPractice(blob, roleplaySlug || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recorder.status, recorder.blob]);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;

      if (e.key === "Escape") {
        setPane((p) => (p === "detail" ? "list" : "rail"));
        return;
      }
      if (!visibleFlags.length) return;

      if (e.key === "j" || e.key === "k") {
        const idx = visibleFlags.findIndex((f) => f.id === selectedFlag?.id);
        const nextIdx = Math.min(visibleFlags.length - 1, Math.max(0, (idx === -1 ? 0 : idx) + (e.key === "j" ? 1 : -1)));
        const next = visibleFlags[nextIdx];
        setActivePanel(null);
        void selectFlag(next.id);
        setLiveMsg(`${next.said} becomes ${next.corrected}, ${next.category}`);
        e.preventDefault();
        return;
      }
      if ((e.key === "m" || e.key === "s") && selectedFlag && connectionOk && !activePanel) {
        void updateFlagStatus(selectedFlag.id, e.key === "m" ? "mastered" : "skipped");
        return;
      }
      if (e.key === "Enter" && selectedFlag && connectionOk && !attempt && !activePanel) {
        setPane("detail");
        if (practicePhase === "typed") {
          document.getElementById("practice-input")?.focus();
        } else {
          setPracticePhase("listening");
          void recorder.start();
        }
        e.preventDefault();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visibleFlags, selectedFlag, connectionOk, attempt, practicePhase, activePanel]);

  function pickCategory(name: string) {
    setCategory(name);
    setActivePanel(null);
    const list = name === "All" ? flags : flags.filter((f) => f.category === name);
    if (list.length) void selectFlag(list[0].id);
    setPane("list");
  }

  function pickRow(flag: Flag) {
    setActivePanel(null);
    void selectFlag(flag.id);
    setPane("detail");
  }

  function startListening() {
    setPracticePhase("listening");
    void recorder.start();
  }

  function goNextFlag() {
    if (!selectedFlag) return;
    const idx = visibleFlags.findIndex((f) => f.id === selectedFlag.id);
    const next = visibleFlags[Math.min(visibleFlags.length - 1, idx + 1)];
    if (next) void selectFlag(next.id);
  }

  async function hearAgain() {
    if (!selectedFlag) return;
    try {
      const blob = await apiClient.synthesizeSpeech(selectedFlag.corrected);
      setHeardUrl(URL.createObjectURL(blob));
      setLiveMsg("Playing the corrected sentence.");
    } catch {
      setLiveMsg("Couldn't play the audio.");
    }
  }

  const selIdx = selectedFlag ? visibleFlags.findIndex((f) => f.id === selectedFlag.id) : -1;
  const remaining = selIdx === -1 ? 0 : Math.max(0, visibleFlags.length - selIdx - 1);

  const practiceHead = selectedFlag && (
    <>
      <p className="lede">Now say it the way you meant it.</p>
      <p className="target">{selectedFlag.corrected}</p>
      <div className="scene">
        <label htmlFor="practice-roleplay">Scene</label>
        <select id="practice-roleplay" value={roleplaySlug} onChange={(e) => setRoleplaySlug(e.target.value)}>
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
      </div>
    </>
  );

  function renderPractice() {
    if (!selectedFlag) return null;

    if (practicePhase === "listening") {
      return (
        <div className="practice">
          {practiceHead}
          <div className="mic-row">
            <button type="button" className="mic live" onClick={() => recorder.stop()}>
              <span className="dot" aria-hidden="true" />
              Listening — tap to stop
            </button>
            <span className="rec-time">
              {clock(elapsed)} / {MAX_CLOCK}
            </span>
          </div>
          <p className="hint">
            Say the whole sentence once, at your own pace. Stopping sends it straight to be transcribed and graded.
          </p>
        </div>
      );
    }
    if (practicePhase === "scoring") {
      return (
        <div className="practice" aria-busy="true">
          {practiceHead}
          <div className="working">
            <Spinner />
            <p className="kicker">Transcribing, then grading</p>
          </div>
          <div className="sk-rows" aria-hidden="true">
            <div className="sk" />
            <div className="sk" />
            <div className="sk short" />
          </div>
          <button type="button" className="alt" onClick={() => setPracticePhase("idle")}>
            Cancel and record again
          </button>
        </div>
      );
    }
    if (practicePhase === "denied") {
      return (
        <div className="practice">
          {practiceHead}
          <div className="notice">
            <span className="lbl">Microphone blocked</span>
            <p>
              This page cannot reach the mic. Allow it from the icon in the address bar, then try again — or type the
              sentence instead, which grades identically.
            </p>
            <span className="detail-txt">{recorder.error ?? "NotAllowedError · getUserMedia"}</span>
          </div>
          <div className="row-btns">
            <button type="button" className="ghost" onClick={() => setPracticePhase("idle")}>
              Try the mic again
            </button>
            <button type="button" className="alt" onClick={() => setPracticePhase("typed")}>
              Type it instead
            </button>
          </div>
        </div>
      );
    }
    if (practicePhase === "nospeech") {
      return (
        <div className="practice">
          {practiceHead}
          <div className="notice">
            <span className="lbl">Nothing came through</span>
            <p>The mic recorded, but no words were recognised. Move a little closer and say it once more — or type it instead.</p>
            <span className="detail-txt">
              {lastRecordedSeconds != null ? `0 words · ${lastRecordedSeconds.toFixed(1)}s of audio` : "0 words recognised"}
            </span>
          </div>
          <div className="row-btns">
            <button type="button" className="ghost" onClick={startListening}>
              Record again
            </button>
            <button type="button" className="alt" onClick={() => setPracticePhase("typed")}>
              Type it instead
            </button>
          </div>
        </div>
      );
    }
    if (practicePhase === "typed") {
      return (
        <form
          className="practice"
          onSubmit={(e) => {
            e.preventDefault();
            if (attemptText.trim()) void submitPractice(attemptText, roleplaySlug || undefined);
          }}
        >
          {practiceHead}
          <div className="typed">
            <input
              id="practice-input"
              type="text"
              value={attemptText}
              onChange={(e) => setAttemptText(e.target.value)}
              placeholder={selectedFlag.corrected}
              autoComplete="off"
              spellCheck={false}
              aria-label="Type your answer"
              autoFocus
            />
            <button type="submit" className="primary" disabled={!attemptText.trim()}>
              Log this
            </button>
          </div>
          <button type="button" className="alt" onClick={() => setPracticePhase("idle")}>
            or use the mic
          </button>
        </form>
      );
    }
    return (
      <div className="practice">
        {practiceHead}
        <button type="button" className="mic" onClick={startListening}>
          <span className="dot" aria-hidden="true" />
          Tap to speak
        </button>
        <button type="button" className="alt" onClick={() => setPracticePhase("typed")}>
          or type it instead
        </button>
      </div>
    );
  }

  function renderDetail() {
    if (activePanel === "dictation") {
      return (
        <>
          <p className="kicker">Dictation</p>
          <h2 className="pair-hd">Type a sentence back</h2>
          <DictationPanel />
        </>
      );
    }
    if (activePanel === "replay") {
      return (
        <>
          <p className="kicker">Listen back</p>
          <h2 className="pair-hd">Last session, with its flags on the timeline</h2>
          <ReplayPanel />
        </>
      );
    }
    if (!selectedFlag) {
      return <p className="placeholder">Nothing to review. Go talk to it.</p>;
    }

    const occurrenceCount = occurrenceByCategory.get(selectedFlag.category) ?? 0;
    const status = selectedFlag.status ?? "open";

    if (!connectionOk) {
      return (
        <>
          <p className="kicker">{selectedFlag.category}</p>
          <h2 className="pair-hd">
            <span className="was">{selectedFlag.said}</span>
            <span className="arrow">becomes</span>
            <span className="now">{selectedFlag.corrected}</span>
          </h2>
          <div className="actions">
            <button type="button" className={status === "mastered" ? "act" : "act solid"} disabled>
              {status === "mastered" ? "Mastered" : "Mark mastered"}
              <kbd>m</kbd>
            </button>
            <button type="button" className="act" disabled>
              Skip for now
              <kbd>s</kbd>
            </button>
            <button type="button" className="act" disabled>
              Hear it again
            </button>
          </div>
          <p className="wait">
            The correction is yours already. The grounded explanation and the grade both need the server, so they wait —
            nothing you say now would be scored.
          </p>
        </>
      );
    }

    if (attempt) {
      const mastered = attempt.mastered;
      return (
        <>
          <div className="logged-head">
            <div className={mastered ? "ring" : "ring again"} aria-hidden="true">
              <svg width="15" height="15" viewBox="0 0 20 20" fill="none">
                {mastered ? (
                  <path
                    d="M4.5 10.4 8.2 14 15.5 6.4"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ) : (
                  <path d="M10 5v6m0 3.2v.3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                )}
              </svg>
            </div>
            <div className="st">
              {mastered ? "Mastered" : "Logged"} <span className={mastered ? "grade" : "grade again"}>({attempt.grade})</span>
            </div>
          </div>
          <p className="kicker">{selectedFlag.category}</p>
          <p className="logged">
            You said it back as <q>{attempt.attempt_text}</q> — that&rsquo;s the one.{" "}
            {mastered
              ? "This pattern is marked resolved; you will not be pushed at it for a while."
              : "It is saved with the flag, so it comes round again before it sticks."}
          </p>
          {attemptHeardSeconds != null && (
            <p className="heard">heard · azure es-ES · {attemptHeardSeconds.toFixed(1)}s</p>
          )}
          <div className="next">
            <button type="button" className="primary" onClick={goNextFlag}>
              Next flag
            </button>
            <span>
              <span className="num">{remaining}</span> left in this pattern.
            </span>
          </div>
        </>
      );
    }

    return (
      <>
        <p className="kicker">
          {selectedFlag.category} · {formatClockTime(selectedFlag.timestamp)}
          {occurrenceCount > 1 ? ` · ${occurrenceCount}× this pattern` : ""}
        </p>
        <h2 className="pair-hd">
          <span className="was">{selectedFlag.said}</span>
          <span className="arrow">becomes</span>
          <span className="now">{selectedFlag.corrected}</span>
        </h2>
        <div className="actions">
          <button
            type="button"
            className={status === "mastered" ? "act" : "act solid"}
            onClick={() => void updateFlagStatus(selectedFlag.id, "mastered")}
          >
            {status === "mastered" ? "Mastered" : "Mark mastered"}
            <kbd>m</kbd>
          </button>
          <button type="button" className="act" onClick={() => void updateFlagStatus(selectedFlag.id, "skipped")}>
            Skip for now
            <kbd>s</kbd>
          </button>
          <button type="button" className="act" onClick={() => void hearAgain()}>
            Hear it again
          </button>
        </div>

        {error && <p className="conn-error">{error}</p>}
        {!explanation && <p className="looking">Looking it up…</p>}
        {explanation && (
          <div className="explain">
            <p>{explanation.explanation}</p>
            <div className="source">
              <span className="lbl">Source</span>
              <a href={explanation.source_url} target="_blank" rel="noreferrer">
                {explanation.source_url}
              </a>
              {explanation.source_excerpt && <blockquote className="excerpt">{explanation.source_excerpt}</blockquote>}
            </div>
          </div>
        )}

        {explanation && renderPractice()}
        {heardUrl && <audio src={heardUrl} autoPlay aria-hidden="true" />}
      </>
    );
  }

  return (
    <div className="review-shell" data-pane={pane}>
      <div className="shell">
        <header className="topbar">
          <h1>Review</h1>
          <span className="meta">
            {sessionMinutes != null && (
              <>
                <span className="num">{sessionMinutes}</span> min ·{" "}
              </>
            )}
            <span className="num">{flags.length}</span> flagged
          </span>
          <span className="spacer" />
          {taskOutcome && flags.length > 0 && (
            <span className="task" data-outcome={taskOutcome.outcome ?? "pending"} title={taskOutcome.success_condition}>
              <span className="mark" aria-hidden="true" />
              {taskOutcome.label}:{" "}
              {taskOutcome.outcome === "success"
                ? "Task complete"
                : taskOutcome.outcome === "fail"
                  ? "Task not completed"
                  : "Not judged yet"}
            </span>
          )}
        </header>

        {!connectionOk && hasCachedList && (
          <div className="banner" role="status">
            <b>Offline</b>
            <span>You can read the list. Explanations and grading come from the server, so those wait.</span>
          </div>
        )}

        <div className="navbar">
          <button className="back" type="button" onClick={() => setPane(pane === "detail" ? "list" : "rail")}>
            <BackIcon />
            <span>{pane === "detail" ? "Flags" : "Patterns"}</span>
          </button>
          <span className="where">
            {pane === "rail"
              ? "Patterns"
              : pane === "list"
                ? category === "All"
                  ? "All flags"
                  : category
                : activePanel === "dictation"
                  ? "Dictation"
                  : activePanel === "replay"
                    ? "Listen back"
                    : "Detail"}
          </span>
        </div>

        <div className="panes">
          <nav className="rail" aria-label="Grammar patterns and other practice">
            <h2>Patterns</h2>
            {flags.length > 0 ? (
              <div id="cats">
                {categoryList.map((c) => (
                  <button
                    key={c.name}
                    type="button"
                    className="cat-btn"
                    aria-pressed={category === c.name}
                    onClick={() => pickCategory(c.name)}
                  >
                    <span className="nm">{c.name}</span>
                    <span className="n">{c.n}</span>
                  </button>
                ))}
              </div>
            ) : (
              hasLoaded && <p className="note">No patterns yet — nothing was flagged in the last session.</p>
            )}
            {flags.length > 0 && repeatCategoryCount > 0 && (
              <p className="note repeat">
                Repeats carry across sessions. <span className="num">{repeatCategoryCount}</span> of these have come up
                before.
              </p>
            )}
            {connectionOk && (
              <>
                <div className="divide" />
                <h2 className="later">Other practice</h2>
                <div className="entries">
                  {flags.length > 0 && (
                    <button
                      className="entry"
                      type="button"
                      onClick={() => {
                        setActivePanel("dictation");
                        setPane("detail");
                      }}
                    >
                      <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                        <path d="M3 6h14M3 10h9M3 14h11" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
                      </svg>
                      Dictation
                      <span className="sub-n">type back</span>
                    </button>
                  )}
                  <button
                    className="entry"
                    type="button"
                    onClick={() => {
                      setActivePanel("replay");
                      setPane("detail");
                    }}
                  >
                    <svg width="15" height="15" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                      <path d="M7 5.5v9l7-4.5-7-4.5Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
                    </svg>
                    Listen back
                    {replayDurationSeconds != null && <span className="sub-n">{clock(replayDurationSeconds * 1000)}</span>}
                  </button>
                </div>
              </>
            )}
          </nav>

          <div className="list">
            {flags.length > 0 && (
              <div className="list-hd">
                <span className="t">{category === "All" ? "All flags" : category}</span>
                <span className="c">{visibleFlags.length}</span>
              </div>
            )}

            {!hasLoaded && !connectionOk && (
              <div className="empty">
                <p className="big">Can&rsquo;t check for flags right now.</p>
              </div>
            )}
            {hasLoaded && flags.length === 0 && (
              <div className="empty">
                <p className="big">Nothing was flagged last time.</p>
                <p className="small">
                  That happens — it usually means you stayed inside what you already know. Start a longer session and push
                  at something harder.
                </p>
              </div>
            )}

            {visibleFlags.length > 0 && (
              <div className="rows">
                {visibleFlags.map((flag) => {
                  const occurrenceCount = occurrenceByCategory.get(flag.category) ?? 0;
                  const status = flag.status ?? "open";
                  const isSelected = flag.id === selectedFlag?.id && !activePanel;
                  return (
                    <button
                      key={flag.id}
                      ref={(el) => {
                        if (el) rowRefs.current.set(flag.id, el);
                        else rowRefs.current.delete(flag.id);
                      }}
                      className="row"
                      type="button"
                      data-status={status}
                      aria-current={isSelected ? "true" : undefined}
                      disabled={!connectionOk}
                      onClick={() => pickRow(flag)}
                    >
                      <span className="dot" aria-hidden="true" />
                      <span>
                        <span className="pair">
                          <span className="was">{flag.said}</span>
                          <span className="arrow">becomes</span>
                          <span className="now">{flag.corrected}</span>
                        </span>
                        <span className="sub">
                          <span className="cat">{flag.category}</span>
                          {occurrenceCount > 1 && <span className="tag">{occurrenceCount}× this pattern</span>}
                          {status === "mastered" && <span className="tag muted">Mastered</span>}
                          {status === "skipped" && <span className="tag muted">Skipped</span>}
                        </span>
                      </span>
                      <span className="at">{formatClockTime(flag.timestamp)}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {flags.length > 0 && (
              <div className="khint">
                <span>
                  <kbd>j</kbd>
                  <kbd>k</kbd>move
                </span>
                <span>
                  <kbd>m</kbd>mastered
                </span>
                <span>
                  <kbd>s</kbd>skip
                </span>
                <span>
                  <kbd>↵</kbd>speak it
                </span>
              </div>
            )}
          </div>

          <main className="detail">{renderDetail()}</main>
        </div>
      </div>

      <p className="sr" role="status" aria-live="polite">
        {liveMsg}
      </p>
    </div>
  );
}
