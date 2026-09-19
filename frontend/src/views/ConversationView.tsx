import { useEffect, useRef, useState } from "react";
import "./ConversationView.css";
import { useSessionState } from "../hooks/useSessionState";
import { useMicPermission } from "../hooks/useMicPermission";
import { useConnectionStore } from "../state/connectionStore";
import { apiClient } from "../api/client";
import type { SessionRecap, SessionScenario, TurnState } from "../api/types";
import { ROLEPLAY_SCENARIOS } from "../data/roleplayScenarios";
import { DueBrief } from "../components/DueBrief";

// C2 post-session recap card. Plain summary, not a celebratory screen --
// this is a personal single-user app (see CLAUDE.md's "deprioritize social/
// gamification framing" memory note). Dismissible so it doesn't sit in the
// way of starting the next session.
function SessionRecapCard({ recap, onDismiss }: { recap: SessionRecap; onDismiss: () => void }) {
  return (
    <div className="recap-card">
      <button type="button" className="recap-dismiss" onClick={onDismiss} aria-label="Dismiss">
        ×
      </button>
      <p className="kicker">Session recap</p>
      <p className="recap-flags">
        {recap.flag_count === 0
          ? "No flags this session."
          : `${recap.flag_count} flag${recap.flag_count === 1 ? "" : "s"} this session`}
      </p>
      {recap.categories_flagged.length > 0 && (
        <p className="recap-categories">{recap.categories_flagged.join(", ")}</p>
      )}
    </div>
  );
}

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

// D5 pressure dial: sends only the level token now -- the backend owns all
// pacing prose (TTS rate, lexical range, rescue timing) next to the system
// prompt it modifies, per decisions/feature-plan-D5-pressure-dial-2026-09-18.md
// §5.5. Replaces D3's frontend-authored phrase folded into scenarioText.
const PRESSURE_LEVELS: { key: "gentle" | "normal" | "push"; label: string }[] = [
  { key: "gentle", label: "Gentle" },
  { key: "normal", label: "Normal" },
  { key: "push", label: "Push" },
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

// Prefill for the free-text scene field -- pacing/proficiency framing is
// D5's backend-owned pressure prompt block now, not composed here.
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

  const scenarioText = sceneText.trim();
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

  // Fetch the recap once per stop, not on every render while stopped --
  // wasRunningRef tracks the previous status.running so the effect only
  // fires on the running -> stopped transition, mirroring the "fetch once
  // while idle" shape useSessionState already uses for the scenario picker.
  const [recap, setRecap] = useState<SessionRecap | null>(null);
  const wasRunningRef = useRef(status.running);
  useEffect(() => {
    if (wasRunningRef.current && !status.running) {
      apiClient
        .getSessionRecap()
        .then(setRecap)
        .catch(() => {}); // optional, never load-bearing for starting the next session
    }
    wasRunningRef.current = status.running;
  }, [status.running]);

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
            <DueBrief due={scenario?.due_patterns} />
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
                <label className="field-label" htmlFor="roleplay-select">
                  Or pick a roleplay
                </label>
                <select
                  id="roleplay-select"
                  className="scene-input"
                  value=""
                  onChange={(e) => {
                    const picked = ROLEPLAY_SCENARIOS.find((s) => s.slug === e.target.value);
                    if (picked) {
                      setSceneText(picked.setting);
                      setSceneEdited(true);
                    }
                  }}
                >
                  <option value="" disabled>
                    Choose a scenario…
                  </option>
                  {ROLEPLAY_SCENARIOS.map((s) => (
                    <option key={s.slug} value={s.slug}>
                      {s.label}
                    </option>
                  ))}
                </select>
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
                setRecap(null);
                start(scenarioText || undefined, sessionLength ?? undefined, pressure);
                setSceneEdited(false);
              }
            }}
          >
            {status.running ? "Stop" : "Start"}
          </button>
        )}
      </div>

      {recap && <SessionRecapCard recap={recap} onDismiss={() => setRecap(null)} />}

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
