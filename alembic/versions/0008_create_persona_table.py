"""create persona table

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-19

Persona storage. Column shape is the one the user signed off on:
    persona(id, slug, name, setting, memory, updated_at)
`slug` is unique. `memory` is nullable (no memory until first session with
that persona). Static persona definitions live in api/data/ later; this table
holds the row plus memory. No foreign key to learner_profile -- single-user
project, same reasoning as 0003_create_session_log_table.py.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "persona",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("setting", sa.Text(), nullable=False),
        sa.Column("memory", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_persona_slug"),
    )


def downgrade() -> None:
    op.drop_table("persona")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0006 -- runs the real DDL.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("persona")}
        assert set(columns) == {"id", "slug", "name", "setting", "memory", "updated_at"}, columns
        assert columns["memory"]["nullable"] is True
        for name in columns.keys() - {"memory", "id"}:
            assert columns[name]["nullable"] is False, name
        uniques = inspect(conn).get_unique_constraints("persona")
        assert [u["column_names"] for u in uniques] == [["slug"]], uniques

        with Operations.context(ctx):
            downgrade()
        assert inspect(conn).get_table_names() == []

    print("0008_create_persona_table self-check passed")
