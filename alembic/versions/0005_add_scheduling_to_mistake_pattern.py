"""add interval_days and next_due_at to mistake_pattern

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-19

Backs roadmap item A1 (mistake half-life scheduler). `interval_days` is the
current review interval (server_default 1.0, so existing rows get a valid
value); `next_due_at` is nullable -- NULL means "never scheduled yet".
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mistake_pattern", sa.Column("interval_days", sa.Float(), server_default="1.0", nullable=False))
    op.add_column("mistake_pattern", sa.Column("next_due_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("mistake_pattern", "next_due_at")
    op.drop_column("mistake_pattern", "interval_days")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0004 -- runs the real DDL.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            op.create_table("mistake_pattern", sa.Column("id", sa.Integer(), primary_key=True))
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("mistake_pattern")}
        assert columns["interval_days"]["nullable"] is False, columns
        assert columns["next_due_at"]["nullable"] is True, columns

        with Operations.context(ctx):
            downgrade()
        columns_after = {c["name"] for c in inspect(conn).get_columns("mistake_pattern")}
        assert not {"interval_days", "next_due_at"} & columns_after

    print("0005_add_scheduling_to_mistake_pattern self-check passed")
