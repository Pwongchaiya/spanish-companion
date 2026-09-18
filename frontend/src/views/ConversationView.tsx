import { useEffect, useRef, useState } from "react";
import "./ConversationView.css";
import { useSessionState } from "../hooks/useSessionState";
import { useMicPermission } from "../hooks/useMicPermission";
import { useConnectionStore } from "../state/connectionStore";
import type { SessionScenario, TurnState } from "../api/types";

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

// Composes the same "Speak at a {level} level. Focus this session on:
// {topic}." shape the backend's own default-scenario fallback uses
// (api/exposers/voice_conversation.py::_default_scenario_text), so the
// text a user sees and edits here matches what an un-overridden session
// would open with.
function composeScenarioText(scenario: SessionScenario): string {
  const parts = [`Speak at a ${scenario.proficiency_level} proficiency level.`];
  if (scenario.suggested_topic) {
    parts.push(`Focus this session on: ${scenario.suggested_topic}.`);
  }
  return parts.join(" ");
}

export function ConversationView() {
  const { status, transcript, turnState, scenario, start, stop } = useSessionState();
  const mic = useMicPermission();
  const [scenarioText, setScenarioText] = useState("");
  const [scenarioEdited, setScenarioEdited] = useState(false);

  // Reset to the freshly-fetched suggestion whenever a new one arrives,
  // unless the user has already started typing their own override --
  // scenarioEdited is cleared on stop() below so the next idle period
  // starts from the new suggestion again, not a stale hand-typed one.
  useEffect(() => {
    if (scenario && !scenarioEdited) setScenarioText(composeScenarioText(scenario));
  }, [scenario, scenarioEdited]);
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
  // Once a suggestion has loaded, the editable scenario field below takes
  // over the idle hint's spot entirely -- falls back to the old static
  // hint if the fetch hasn't resolved yet (or failed; the picker is
  // optional, never load-bearing for starting a conversation).
  const showScenarioPicker = connectionOk && !status.running && !!scenario;
  const hint = !connectionOk
    ? CONNECTION_HINT[phase]
    : showScenarioPicker
      ? null
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
        {showScenarioPicker && (
          <textarea
            className="scenario-input"
            aria-label="Session scenario"
            rows={2}
            value={scenarioText}
            onChange={(e) => {
              setScenarioText(e.target.value);
              setScenarioEdited(true);
            }}
          />
        )}
        {phase !== "retrying" && (
          <button
            className="conversation-toggle"
            disabled={!connectionOk}
            onClick={() => {
              if (status.running) {
                stop();
              } else {
                start(scenarioText.trim() || undefined);
                setScenarioEdited(false);
              }
            }}
          >
            {status.running ? "Stop" : "Start"}
          </button>
        )}
      </div>

      {/* ponytail: WebRTC spike step, standalone mic-permission check, not wired
          to backend signaling yet. See
          decisions/voice-conversation-browser-webrtc-transport.md. */}
      <button className="conversation-toggle" onClick={mic.requestMic}>
        {mic.status === "idle" && "Request mic access"}
        {mic.status === "granted" && "Mic access granted"}
        {mic.status === "denied" && "Mic access denied — retry"}
        {mic.status === "error" && `Mic error: ${mic.error}`}
      </button>

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
