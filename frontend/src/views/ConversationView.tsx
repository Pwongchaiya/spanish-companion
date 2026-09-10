import "./ConversationView.css";
import { useSessionState } from "../hooks/useSessionState";
import { useConnectionStore } from "../state/connectionStore";
import type { TurnState } from "../api/types";

const TURN_STATE_LABELS: Record<Exclude<TurnState, null>, string> = {
  listening: "Listening",
  thinking: "Thinking…",
  speaking: "Speaking",
  idle: "Listening",
};

function stateLabel(running: boolean, ready: boolean, turnState: TurnState): string {
  if (!running) return "Stopped";
  if (!ready) return "Warming up…";
  return turnState ? TURN_STATE_LABELS[turnState] : "Listening";
}

export function ConversationView() {
  const { status, transcript, turnState, start, stop } = useSessionState();
  const connectionOk = useConnectionStore((s) => s.phase === "ok");
  // listening/idle share the "ready" ring state -- only thinking/speaking
  // get their own state, per ring CSS below.
  const ringState = !status.running
    ? "stopped"
    : !status.ready
      ? "warming"
      : turnState === "thinking" || turnState === "speaking"
        ? turnState
        : "ready";

  return (
    <div className="view">
      <div className="breath">
        <div className={`ring ${ringState}`} aria-hidden="true" />
        <p className="status-label">{stateLabel(status.running, status.ready, turnState)}</p>
        <button
          className="primary conversation-toggle"
          disabled={!connectionOk}
          onClick={status.running ? stop : start}
        >
          {status.running ? "Stop" : "Start"}
        </button>
      </div>

      <div className="transcript">
        {transcript.length === 0 && <p className="empty">No conversation yet — press Start and talk.</p>}
        {transcript.map((turn, i) => (
          <div key={i} className={`turn ${turn.role}`}>
            <span className="role">{turn.role === "user" ? "You" : "Companion"}</span>
            <p>{turn.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
