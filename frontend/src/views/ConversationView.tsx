import { useSessionState } from "../hooks/useSessionState";
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
  const { status, transcript, turnState, connectionStatus, error, start, stop } = useSessionState();
  // listening/idle share the "ready" (green) dot -- only thinking/speaking
  // get their own color, per App.css.
  const dotClass = !status.running
    ? "stopped"
    : !status.ready
      ? "warming"
      : turnState === "thinking" || turnState === "speaking"
        ? turnState
        : "ready";

  return (
    <div className="view">
      {error && <p className="conn-error">{error}</p>}
      <div className="status-row">
        <span className={`status-dot ${dotClass}`} />
        <span>{stateLabel(status.running, status.ready, turnState)}</span>
        {connectionStatus === "error" && <span className="conn-error">connection lost</span>}
        <button className="primary" onClick={status.running ? stop : start}>
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
