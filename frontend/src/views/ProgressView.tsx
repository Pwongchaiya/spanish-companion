import { useProgress } from "../hooks/useProgress";
import "./ProgressView.css";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function ProgressView() {
  const { mistakes, topics, hasLoaded } = useProgress();
  const activeMistakes = mistakes.filter((m) => m.status === "active");
  const coveredCount = topics.filter((t) => t.covered).length;

  return (
    <div className="view progress-view">
      <section>
        <p className="kicker">Recurring mistakes</p>
        {mistakes.length === 0 && (
          <p className="empty">{hasLoaded ? "Nothing recurring yet. That's a good sign." : "Loading…"}</p>
        )}
        {activeMistakes.length > 0 && (
          <div className="pattern-list">
            {activeMistakes
              .slice()
              .sort((a, b) => b.occurrence_count - a.occurrence_count)
              .map((pattern) => (
                <div className="pattern-row" key={pattern.id}>
                  <span className="pattern-cat">{pattern.category}</span>
                  <span className="pattern-count">
                    {pattern.occurrence_count}× · last {formatDate(pattern.last_seen_at)}
                  </span>
                </div>
              ))}
          </div>
        )}
      </section>

      <section>
        <p className="kicker">Corpus coverage</p>
        {hasLoaded && topics.length > 0 && (
          <p className="coverage-summary">
            {coveredCount} / {topics.length} topics covered
          </p>
        )}
        {topics.length > 0 && (
          <div className="topic-list">
            {topics.map((entry) => (
              <div className="topic-row" key={entry.topic}>
                <span className={entry.covered ? "topic-dot covered" : "topic-dot"} aria-hidden="true" />
                <span className="topic-name">{entry.topic}</span>
                {entry.covered && entry.first_covered_at && (
                  <span className="topic-date">since {formatDate(entry.first_covered_at)}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
