"""create session_log table

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-18

Backs roadmap items C1 (speaking-hours meter) and C3 (longest unflagged
stretch), both parked until now for exactly this reason -- neither
per-session duration nor cross-session flag history existed in any
queryable store (see
Obsidian wiki/decisions/progress-dashboard-scope-c1-c3-parked.md).

Column shape is the one the user signed off on, not invented here:
    session_log(id, started_at, ended_at, flag_count)
`ended_at` is nullable on purpose -- a row is inserted when the voice
pipeline starts and completed when it stops, so a crashed/killed session
leaves ended_at NULL. Both aggregates skip those rows rather than guess a
duration or trust a flag_count that was never written.

No foreign key to learner_profile: this project is explicitly single-user
(state.md / CLAUDE.md), and every other Progress read already resolves the
singleton profile itself. Adding profile_id here would be speculative
generality for G2 ("un-singleton LearnerProfile"), which the roadmap
deliberately does not plan.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "started_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "flag_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("session_log")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as
    # 0002_create_learner_profile_tables.py -- runs the real DDL rather than
    # asserting on the op.* call args, so a malformed column type fails here
    # instead of against live Postgres.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        assert "session_log" in inspect(conn).get_table_names()
        columns = {c["name"]: c for c in inspect(conn).get_columns("session_log")}
        assert set(columns) == {"id", "started_at", "ended_at", "flag_count"}, columns
        assert columns["ended_at"]["nullable"] is True, "ended_at must stay nullable for in-flight sessions"
        assert columns["started_at"]["nullable"] is False
        assert columns["flag_count"]["nullable"] is False

        with Operations.context(ctx):
            downgrade()
        assert inspect(conn).get_table_names() == []

    print("0003_create_session_log_table self-check passed")
