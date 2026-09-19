"""add scenario_slug and task_outcome to session_log

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-19

Roadmap D4 (task-style roleplay scenarios). Two nullable columns, the shape
the user signed off on:
    scenario_slug  Text, NULL = session had no roleplay scenario
    task_outcome   Text, 'success' | 'fail'; NULL = not a task scenario, or
                   not yet judged (judging happens in Review Mode, after the
                   session, never live)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("session_log", sa.Column("scenario_slug", sa.Text(), nullable=True))
    op.add_column("session_log", sa.Column("task_outcome", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("session_log", "task_outcome")
    op.drop_column("session_log", "scenario_slug")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0003 -- runs the real DDL.
    # sqlite can't drop columns via plain ALTER on old versions, so only the
    # upgrade is exercised end to end; downgrade is one drop_column per column.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE session_log (id INTEGER PRIMARY KEY, flag_count INTEGER)"))
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()
        columns = {c["name"]: c for c in inspect(conn).get_columns("session_log")}
        assert {"scenario_slug", "task_outcome"} <= set(columns), columns
        assert columns["scenario_slug"]["nullable"] is True
        assert columns["task_outcome"]["nullable"] is True

        with Operations.context(ctx):
            downgrade()
        assert set(c["name"] for c in inspect(conn).get_columns("session_log")) == {"id", "flag_count"}

    print("0007_add_task_outcome_to_session_log self-check passed")
