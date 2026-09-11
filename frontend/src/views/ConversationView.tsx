import { useEffect, useRef } from "react";
import "./ConversationView.css";
import { useSessionState } from "../hooks/useSessionState";
import { useConnectionStore } from "../state/connectionStore";
import type { TurnState } from "../api/types";

// How close to the bottom (px) still counts as "pinned" -- new turns
// auto-scroll into view. Past that, the user is reading history and a
// new turn must not yank their scroll position.
const PIN_THRESHOLD_PX = 40;

const TURN_STATE_LABELS: Record<Exclude<TurnState, null>, string> = {
  listening: "Listening",
  thinking: "Thinking…",
  speaking: "Speaking",
  idle: "Listening",
};

function stateLabel(
  running: boolean,
  ready: boolean,
  turnState: TurnState,
): string {
  if (!running) return "Stopped";
  if (!ready) return "Warming up…";
  return turnState ? TURN_STATE_LABELS[turnState] : "Listening";
}

// Connection-phase copy for the idle/live panel, per the "When Aliento
// Can't Reach the Server" mockup: quiet backoff gets a held ring and no
// button at all (nothing to press while a retry is already in flight);
// a give-up gets a named state, an explanation, and a disabled button
// rather than a hidden one, so the person can see why it can't be pressed.
const CONNECTION_LABEL: Record<"retrying" | "down", string> = {
  retrying: "Holding",
  down: "Offline",
};
const CONNECTION_HINT: Record<"retrying" | "down", string> = {
  retrying: "Give it a second. Your last conversation is still here.",
  down: "Starting a conversation needs the server. Reading this one doesn't.",
};

export function ConversationView() {
  const { status, transcript, turnState, start, stop } = useSessionState();
  const phase = useConnectionStore((s) => s.phase);
  const connectionOk = phase === "ok";
  // listening/idle share the "ready" ring state -- only thinking/speaking
  // get their own state, per ring CSS below.
  const ringState = !status.running
    ? "stopped"
    : !status.ready
      ? "warming"
      : turnState === "thinking" || turnState === "speaking"
        ? turnState
        : "ready";

  const label = !connectionOk
    ? CONNECTION_LABEL[phase]
    : status.running
      ? stateLabel(status.running, status.ready, turnState)
      : null;
  const hint = !connectionOk
    ? CONNECTION_HINT[phase]
    : transcript.length === 0
      ? "press Start and talk"
      : null;

  const transcriptRef = useRef<HTMLDivElement>(null);
  const pinnedRef = useRef(true);

  const handleScroll = () => {
    const el = transcriptRef.current;
    if (!el) return;
    pinnedRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight < PIN_THRESHOLD_PX;
  };

  useEffect(() => {
    const el = transcriptRef.current;
    if (el && pinnedRef.current) el.scrollTop = el.scrollHeight;
  }, [transcript]);

  return (
    <div className="view conversation-view">
      <div className="breath">
        <div className={`ring ${ringState}`} aria-hidden="true" />
        {label && <p className="status-label">{label}</p>}
        {hint && <p className="hint">{hint}</p>}
        {phase !== "retrying" && (
          <button
            className="conversation-toggle"
            disabled={!connectionOk}
            onClick={status.running ? stop : start}
          >
            {status.running ? "Stop" : "Start"}
          </button>
        )}
      </div>

      <div className="transcript" ref={transcriptRef} onScroll={handleScroll}>
        {transcript.map((turn, i) => (
          <div key={i} className={`turn ${turn.role}`}>
            <span className="role">
              {turn.role === "user" ? "You" : "Companion"}
            </span>
            <p>{turn.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
