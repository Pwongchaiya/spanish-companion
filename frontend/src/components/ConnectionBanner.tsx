import { useConnectionStore } from "../state/connectionStore";
import "./ConnectionBanner.css";

// One banner, app-wide, directly under the header -- per-view .conn-error
// text is deleted (Aliento error-handling mockup). Presentational only;
// all the logic lives in connectionStore + useBackoffRetry.
export function ConnectionBanner() {
  const phase = useConnectionStore((s) => s.phase);
  const attempt = useConnectionStore((s) => s.attempt);
  const maxAttempts = useConnectionStore((s) => s.maxAttempts);
  const message = useConnectionStore((s) => s.message);
  const subMessage = useConnectionStore((s) => s.subMessage);
  const retry = useConnectionStore((s) => s.retry);

  if (phase === "ok") return null;

  return (
    <div className={`conn-banner ${phase === "down" ? "down" : ""}`} role="status">
      <span className="conn-banner__dot" />
      {phase === "retrying" ? (
        <>
          <span className="conn-banner__msg">Reconnecting…</span>
          {maxAttempts > 0 && (
            <span className="conn-banner__att">
              attempt {attempt} of {maxAttempts}
            </span>
          )}
        </>
      ) : (
        <>
          <span className="conn-banner__msg">{message}</span>
          {subMessage && <span className="conn-banner__sub">{subMessage}</span>}
          {retry && (
            <button type="button" className="conn-banner__retry" onClick={retry}>
              Retry
            </button>
          )}
        </>
      )}
    </div>
  );
}
