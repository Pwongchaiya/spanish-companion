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

// D3 pressure dial: replaces the old fixed "Speak at a {level} proficiency
// level" framing with a user-chosen pacing phrase, folded together with the
// free-text scene direction into the single scenarioText string start()
// sends -- see composeStartText below.
const PRESSURE_LEVELS: { key: "gentle" | "normal" | "push"; label: string; phrase: string }[] = [
  { key: "gentle", label: "Gentle", phrase: "Take it gently." },
  { key: "normal", label: "Normal", phrase: "Take it at a normal pace." },
  { key: "push", label: "Push", phrase: "Push me." },
];
const SESSION_LENGTHS = ["5", "10", "20"] as const;

// P2 placement: the mic-permission control (M2 look -- glyph + label,
// state-driven icon) moves from its own standalone button into the
// "+ More to adjust" panel as a setup row, per
// https://claude.ai/artifact/69fYrFAx75s4pf1B44MpAB. Collapsed by default;
// a denied/error state leaks an ember badge onto the closed reveal link so
// a blocked mic is never fully hidden.
const MIC_LABELS: Record<import("../hooks/useMicPermission").MicPermissionStatus, string> = {
  idle: "Grant access",
  granted: "Ready",
  denied: "Blocked — retry",
  error: "Error",
};

function MicGlyph({ state }: { state: import("../hooks/useMicPermission").MicPermissionStatus }) {
  return (
    <svg className="glyph" viewBox="0 0 16 16" aria-hidden="true">
      <rect x="5.5" y="1.5" width="5" height="8" rx="2.5" />
      <path d="M3 7.5a5 5 0 0 0 10 0M8 12.5V15" />
      {state === "denied" && <path d="M2.5 13.5 13.5 2.5" />}
      {state === "error" && (
        <>
          <path d="M8 1.5v4.2" />
          <circle cx="8" cy="8.3" r="0.5" />
        </>
      )}
    </svg>
  );
}

// Prefill for the free-text scene field -- just the topic half of the old
// composeScenarioText, since pressure now carries the proficiency framing.
function composeSceneText(scenario: SessionScenario): string {
  return scenario.suggested_topic ? `Focus this session on: ${scenario.suggested_topic}.` : "";
}

export function ConversationView() {
  const { status, transcript, turnState, scenario, start, stop } = useSessionState();
  const mic = useMicPermission();
  const [pressure, setPressure] = useState<(typeof PRESSURE_LEVELS)[number]["key"]>("normal");
  const [sceneText, setSceneText] = useState("");
  const [sceneEdited, setSceneEdited] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);
  const [sessionLength, setSessionLength] = useState<(typeof SESSION_LENGTHS)[number] | null>(null);

  // Reset to the freshly-fetched suggestion whenever a new one arrives,
  // unless the user has already started typing their own override --
  // sceneEdited is cleared on Start below so the next idle period starts
  // from the new suggestion again, not a stale hand-typed one.
  useEffect(() => {
    if (scenario && !sceneEdited) setSceneText(composeSceneText(scenario));
  }, [scenario, sceneEdited]);

  const pressurePhrase = PRESSURE_LEVELS.find((p) => p.key === pressure)!.phrase;
  const scenarioText = [pressurePhrase, sceneText.trim()].filter(Boolean).join(" ");
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
          <div className="scene-control">
            <div className="pressure-dial" role="group" aria-label="Pressure">
              {PRESSURE_LEVELS.map((p) => (
                <button
                  key={p.key}
                  type="button"
                  className="dial-notch"
                  aria-pressed={pressure === p.key}
                  onClick={() => setPressure(p.key)}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {!panelOpen && (
              <button type="button" className="reveal-more" onClick={() => setPanelOpen(true)}>
                + More to adjust
                {(mic.status === "denied" || mic.status === "error") && (
                  <span className="mic-badge">· Needs mic</span>
                )}
              </button>
            )}

            <div className={`more-panel${panelOpen ? " open" : ""}`}>
              <div className="more-panel-inner">
                <div className="more-panel-head">
                  <span>More to adjust</span>
                  <button type="button" className="done-corner" onClick={() => setPanelOpen(false)}>
                    Done
                  </button>
                </div>
                <label className="field-label" htmlFor="scene-text-input">
                  Set the scene — who should I be?
                </label>
                <input
                  id="scene-text-input"
                  className="scene-input"
                  type="text"
                  maxLength={80}
                  value={sceneText}
                  placeholder="Pretend you're a waiter and I'm ordering…"
                  onChange={(e) => {
                    setSceneText(e.target.value);
                    setSceneEdited(true);
                  }}
                />
                <span className="field-label">Session length</span>
                <div className="pressure-dial" role="group" aria-label="Session length">
                  {SESSION_LENGTHS.map((len) => (
                    <button
                      key={len}
                      type="button"
                      className="dial-notch"
                      aria-pressed={sessionLength === len}
                      onClick={() => setSessionLength((prev) => (prev === len ? null : len))}
                    >
                      {len} min
                    </button>
                  ))}
                </div>
                <div className="more-panel-row">
                  <span className="row-key">Microphone</span>
                  {/* ponytail: WebRTC spike step, standalone mic-permission
                      check, not wired to backend signaling yet. See
                      decisions/voice-conversation-browser-webrtc-transport.md. */}
                  <button
                    type="button"
                    className="mic-control"
                    data-state={mic.status}
                    aria-disabled={mic.status === "granted"}
                    title={mic.status === "error" ? mic.error ?? undefined : undefined}
                    onClick={mic.status === "granted" ? undefined : mic.requestMic}
                  >
                    <MicGlyph state={mic.status} />
                    <span className="mic-label">{MIC_LABELS[mic.status]}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        {phase !== "retrying" && (
          <button
            className="conversation-toggle"
            disabled={!connectionOk}
            onClick={() => {
              if (status.running) {
                stop();
              } else {
                setPanelOpen(false);
                start(scenarioText || undefined, sessionLength ?? undefined);
                setSceneEdited(false);
              }
            }}
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
