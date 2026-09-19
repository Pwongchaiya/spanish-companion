import "./DueBrief.css";
import type { DuePattern } from "../api/types";

// A3: read-only "Due for review" chips. Display only -- the backend already
// appends the priming brief to the bot prompt, so this never feeds scene text.
export function DueBrief({ due }: { due?: DuePattern[] }) {
  if (!due || due.length === 0) return null;
  return (
    <div className="due-brief">
      <span className="field-label">Due for review</span>
      <ul className="due-chips">
        {due.map((d) => (
          <li key={d.category} className="due-chip">
            {d.category.replace(/_/g, " ")}
          </li>
        ))}
      </ul>
    </div>
  );
}
