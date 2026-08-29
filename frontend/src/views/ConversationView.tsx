import { useSessionState } from "../hooks/useSessionState";

function stateLabel(running: boolean, ready: boolean): string {
  if (!running) return "Stopped";
  return ready ? "Listening" : "Warming up…";
}

export function ConversationView() {
  const { status, transcript, connectionStatus, error, start, stop } = useSessionState();

  return (
    <div className="view">
      {error && <p className="conn-error">{error}</p>}
      <div className="status-row">
        <span className={`status-dot ${status.running ? (status.ready ? "ready" : "warming") : "stopped"}`} />
        <span>{stateLabel(status.running, status.ready)}</span>
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
