"""add is_word_drill to pronunciation_result

Revision ID: 0011
Revises: 0010

Marks rows produced by the single-word drill so the progress trend can exclude
them (a one-word score is not comparable to a full-sentence attempt).
Existing rows are backfilled False via the server default.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "pronunciation_result",
        sa.Column("is_word_drill", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("pronunciation_result", "is_word_drill")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0004 -- runs the real DDL.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            op.create_table("pronunciation_result", sa.Column("id", sa.Integer(), primary_key=True))
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("pronunciation_result")}
        assert "is_word_drill" in columns, columns
        assert columns["is_word_drill"]["nullable"] is False

        with Operations.context(ctx):
            downgrade()
        columns_after = {c["name"] for c in inspect(conn).get_columns("pronunciation_result")}
        assert "is_word_drill" not in columns_after

    print("0011_add_is_word_drill_to_pronunciation_result self-check passed")
