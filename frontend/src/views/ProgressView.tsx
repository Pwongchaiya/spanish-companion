import { useProgress } from "../hooks/useProgress";
import "./ProgressView.css";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// C1's "with milestones". A presentation ladder, so it lives here rather
// than in ProgressOrchestrationService -- the service returns raw seconds.
const MILESTONE_HOURS = [1, 5, 10, 25, 50, 100];

export function formatSpoken(totalSeconds: number): string {
  if (totalSeconds < 3600) return `${Math.floor(totalSeconds / 60)} min`;
  return `${(totalSeconds / 3600).toFixed(1)} h`;
}

export function nextMilestone(totalSeconds: number): number | null {
  const hours = totalSeconds / 3600;
  return MILESTONE_HOURS.find((m) => m > hours) ?? null;
}

export function ProgressView() {
  const { mistakes, topics, speaking, streak, hasLoaded } = useProgress();
  const activeMistakes = mistakes.filter((m) => m.status === "active");
  const coveredCount = topics.filter((t) => t.covered).length;
  const upcomingMilestone = speaking ? nextMilestone(speaking.total_seconds) : null;

  return (
    <div className="view progress-view">
      <section className="meters">
        <div className="meter">
          <p className="kicker">Time spoken</p>
          <p className="meter-value">{speaking ? formatSpoken(speaking.total_seconds) : "—"}</p>
          <p className="meter-sub">
            {speaking
              ? `${speaking.session_count} session${speaking.session_count === 1 ? "" : "s"}` +
                (upcomingMilestone ? ` · next ${upcomingMilestone} h` : "")
              : "Loading…"}
          </p>
        </div>

        <div className="meter">
          <p className="kicker">Clean streak</p>
          <p className="meter-value">{streak ? streak.current : "—"}</p>
          <p className="meter-sub">
            {streak ? `sessions with no flags · best ${streak.longest}` : "Loading…"}
          </p>
        </div>
      </section>

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
