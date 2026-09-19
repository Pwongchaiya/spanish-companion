import type { PronunciationTrendPoint } from "../api/types";
import "./PronunciationTrend.css";

const W = 240;
const H = 48;
const PAD = 4;

// ponytail: no chart lib -- one polyline per series on a fixed 0-100 axis.
// A single point has no line, so it draws as a dot.
function points(values: number[]): string {
  const step = values.length > 1 ? (W - 2 * PAD) / (values.length - 1) : 0;
  return values
    .map((v, i) => `${(PAD + i * step).toFixed(1)},${(H - PAD - (Math.max(0, Math.min(100, v)) / 100) * (H - 2 * PAD)).toFixed(1)}`)
    .join(" ");
}

function Sparkline({ label, values, className }: { label: string; values: number[]; className: string }) {
  const first = Math.round(values[0]);
  const last = Math.round(values[values.length - 1]);
  const pts = points(values);
  const [lx, ly] = pts.split(" ").pop()!.split(",");
  return (
    <div className="trend-row">
      <span className="trend-label">{label}</span>
      <svg
        className={`trend-svg ${className}`}
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${label} from ${first} to ${last}`}
      >
        {values.length > 1 && <polyline points={pts} fill="none" strokeWidth="1.5" />}
        <circle cx={lx} cy={ly} r="2.5" />
      </svg>
      <span className="trend-values">
        {first} → {last}
      </span>
    </div>
  );
}

export function PronunciationTrend({ trend, hasLoaded }: { trend: PronunciationTrendPoint[]; hasLoaded: boolean }) {
  if (trend.length === 0) {
    return <p className="empty">{hasLoaded ? "No shadowing attempts yet" : "Loading…"}</p>;
  }
  return (
    <div className="trend">
      <Sparkline label="Accuracy" values={trend.map((p) => p.accuracy)} className="trend-accuracy" />
      <Sparkline label="Fluency" values={trend.map((p) => p.fluency)} className="trend-fluency" />
    </div>
  );
}
