import { useRef, useState } from "react";
import { useSessionReplay } from "../hooks/useSessionReplay";
import { formatOffset, markerPercent, seekTarget } from "../audio/replayTimeline";
import "./ReplayPanel.css";

// E3: listen back to the last session with its flags marked on a timeline.
// Click a marker to seek the audio to just before that mistake.
export function ReplayPanel() {
  const { phase, replay, load } = useSessionReplay();
  const audioRef = useRef<HTMLAudioElement>(null);
  const [currentTime, setCurrentTime] = useState(0);

  function seekTo(offsetSeconds: number) {
    const audio = audioRef.current;
    if (!audio || !replay) return;
    audio.currentTime = seekTarget(offsetSeconds, replay.duration_seconds);
    void audio.play?.();
  }

  return (
    <div className="replay">
      {phase === "idle" && (
        <button className="secondary" type="button" onClick={load}>
          Listen back to last session
        </button>
      )}
      {phase === "loading" && <p className="looking">Loading the recording…</p>}
      {phase === "none" && (
        <p className="hint">No recording of your last session. Recording is off unless AUDIO_RECORD_ENABLED is set.</p>
      )}
      {phase === "error" && <p className="conn-error">Couldn&rsquo;t load the replay.</p>}

      {phase === "ready" && replay && (
        <>
          <audio
            ref={audioRef}
            controls
            preload="metadata"
            src={replay.audio_url}
            onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
          />
          <div className="replay-track" role="group" aria-label="Flags on the session timeline">
            <div
              className="replay-progress"
              style={{ width: `${markerPercent(currentTime, replay.duration_seconds)}%` }}
            />
            {replay.flags.map((flag) => (
              <button
                key={flag.flag_id}
                className="replay-marker"
                type="button"
                style={{ left: `${markerPercent(flag.offset_seconds, replay.duration_seconds)}%` }}
                title={`${formatOffset(flag.offset_seconds)} ${flag.said} → ${flag.corrected}`}
                aria-label={`Jump to ${formatOffset(flag.offset_seconds)}: ${flag.said} becomes ${flag.corrected}`}
                onClick={() => seekTo(flag.offset_seconds)}
              />
            ))}
          </div>
          {replay.flags.length === 0 && <p className="hint">Nothing was flagged in this session.</p>}
        </>
      )}
    </div>
  );
}
