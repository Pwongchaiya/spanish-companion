"""Weekly progress digest CLI (roadmap item C5) -- hand-written, no agent,
per CLAUDE.md's Phase 2 Layer-Agent Mapping ("a script, not an entity").

    python -m api.exposers.progress_digest

Builds the same two reports as ProgressOrchestrationService (reused
directly, no logic duplicated), formats them as one markdown note, and
writes it straight into the Obsidian vault as a plain file -- no MCP/REST
API call, since a vault note is just a markdown file on disk and this
script isn't a Claude session. Run manually whenever a digest is wanted;
no scheduling.

OBSIDIAN_VAULT_PATH is a new required env var for this script only (not
read by the Flask app) -- added to .env.example, never written to the real
.env per CLAUDE.md's "Claude must never edit .env direct" rule.
"""

import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from api.brokers.learner_profile import SqlAlchemyLearnerProfileBroker
from api.brokers.logging import StdlibLoggingBroker
from api.brokers.mistake_pattern.mistake_pattern_broker import SqlAlchemyMistakePatternBroker
from api.brokers.pronunciation_result import SqlAlchemyPronunciationResultBroker
from api.brokers.session_log_entry import SqlAlchemySessionLogEntryBroker
from api.brokers.topic_covered import SqlAlchemyTopicCoveredBroker
from api.models.foundations.mistake_pattern.mistake_pattern import MistakePattern
from api.models.orchestrations.progress.topic_coverage_entry import TopicCoverageEntry
from api.services.foundations.learner_profile import LearnerProfileService
from api.services.foundations.mistake_pattern import MistakePatternService
from api.services.foundations.pronunciation_result import PronunciationResultService
from api.services.foundations.session_log_entry import SessionLogEntryService
from api.services.foundations.topic_covered import TopicCoveredService
from api.services.orchestrations.progress import ProgressOrchestrationService
from api.services.processings.learner_profile import LearnerProfileProcessingService

load_dotenv()


def format_digest(today: date, mistakes: list[MistakePattern], topics: list[TopicCoverageEntry]) -> str:
    """Pure formatting -- no I/O, so this is the self-check's target."""
    active = sorted((m for m in mistakes if m.status == "active"), key=lambda m: m.occurrence_count, reverse=True)
    covered_count = sum(1 for t in topics if t.covered)

    lines = [
        f"# Progress Digest — {today.isoformat()}",
        "",
        "## Recurring mistakes",
    ]
    if active:
        lines += [
            f"- **{m.category}** — {m.occurrence_count}× (last seen {m.last_seen_at.date().isoformat()})"
            for m in active
        ]
    else:
        lines.append("- Nothing recurring right now.")

    lines += [
        "",
        "## Corpus coverage",
        f"{covered_count} / {len(topics)} topics covered" if topics else "No corpus topics ingested yet.",
    ]
    if topics:
        lines += [f"- {'✅' if t.covered else '⬜'} {t.topic}" for t in topics]

    return "\n".join(lines) + "\n"


def main() -> None:
    vault_path = Path(os.environ["OBSIDIAN_VAULT_PATH"])
    database_url = os.environ["DATABASE_URL"]
    logging_broker = StdlibLoggingBroker()

    learner_profile_processing_service = LearnerProfileProcessingService(
        LearnerProfileService(SqlAlchemyLearnerProfileBroker(database_url), logging_broker=logging_broker)
    )
    mistake_pattern_service = MistakePatternService(
        SqlAlchemyMistakePatternBroker(database_url), logging_broker=logging_broker
    )
    topic_covered_service = TopicCoveredService(
        SqlAlchemyTopicCoveredBroker(database_url), logging_broker=logging_broker
    )
    # Roadmap C1/C3 -- the only new broker Progress needed; A5/F1
    # reuse the services already built above.
    session_log_entry_service = SessionLogEntryService(
        SqlAlchemySessionLogEntryBroker(database_url), logging_broker=logging_broker
    )
    progress_service = ProgressOrchestrationService(
        learner_profile_processing_service,
        mistake_pattern_service,
        topic_covered_service,
        session_log_entry_service,
        PronunciationResultService(SqlAlchemyPronunciationResultBroker(database_url), logging_broker=logging_broker),
        logging_broker=logging_broker,
    )

    today = date.today()
    digest = format_digest(today, progress_service.list_mistake_summary(), progress_service.list_topic_coverage())

    out_dir = vault_path / "Projects" / "spanish-companion" / "digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{today.isoformat()}.md"
    out_path.write_text(digest, encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    import sys

    if "--selftest" in sys.argv:
        from datetime import datetime

        no_history = format_digest(date(2026, 1, 1), [], [])
        assert "Nothing recurring right now." in no_history
        assert "No corpus topics ingested yet." in no_history

        def make_pattern(
            pattern_id: int, category: str, occurrence_count: int, day: int, status: str
        ) -> MistakePattern:
            return MistakePattern(
                id=pattern_id,
                profile_id=1,
                category=category,
                occurrence_count=occurrence_count,
                last_seen_at=datetime(2026, 1, day),
                status=status,
            )

        mistakes = [
            make_pattern(1, "gender", 2, 1, "active"),
            make_pattern(2, "ser_estar", 5, 2, "active"),
            make_pattern(3, "subjunctive", 9, 3, "resolved"),
        ]
        topics = [
            TopicCoverageEntry(topic="ser-vs-estar", covered=True, first_covered_at=datetime(2026, 1, 1)),
            TopicCoverageEntry(topic="subjunctive-basics", covered=False, first_covered_at=None),
        ]
        digest = format_digest(date(2026, 9, 18), mistakes, topics)
        assert digest.startswith("# Progress Digest — 2026-09-18")
        assert digest.index("ser_estar") < digest.index("gender"), "not sorted by occurrence_count descending"
        assert "subjunctive" not in digest.split("## Corpus coverage")[0], "resolved pattern must not appear"
        assert "1 / 2 topics covered" in digest
        assert "✅ ser-vs-estar" in digest and "⬜ subjunctive-basics" in digest
        print("progress_digest self-check passed")
    else:
        main()
