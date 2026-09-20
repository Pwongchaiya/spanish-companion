"""create ingestion_queue table

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-19

Roadmap F2 (judge-driven ingestion queue). One row per RAE topic key whose
grounded explanations keep failing the Generation judge:
ingestion_queue(id, topic UNIQUE, weak_verdict_count, status, first_flagged_at,
last_flagged_at). No FK to flags or the learner profile.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingestion_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(), nullable=False, unique=True),
        sa.Column("weak_verdict_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(), server_default="pending", nullable=False),
        sa.Column("first_flagged_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_flagged_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ingestion_queue")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0009 -- runs the real DDL.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("ingestion_queue")}
        assert set(columns) == {
            "id", "topic", "weak_verdict_count", "status", "first_flagged_at", "last_flagged_at"
        }, columns
        for name in columns.keys() - {"id"}:
            assert columns[name]["nullable"] is False, name
        uniques = inspect(conn).get_unique_constraints("ingestion_queue")
        assert [u["column_names"] for u in uniques] == [["topic"]], uniques

        with Operations.context(ctx):
            downgrade()
        assert "ingestion_queue" not in inspect(conn).get_table_names()

    print("0010_create_ingestion_queue_table self-check passed")
