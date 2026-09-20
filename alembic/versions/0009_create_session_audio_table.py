"""create session_audio table

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-19

Roadmap E3 (transcript replay with aligned audio). One row per recorded
session: session_audio(id, session_log_id FK, file_path, duration_seconds,
created_at). The WAV itself lives on local disk under data/audio/.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "session_audio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_log_id", sa.Integer(), sa.ForeignKey("session_log.id"), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("session_audio")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0008 -- runs the real DDL.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(sa.text("CREATE TABLE session_log (id INTEGER PRIMARY KEY)"))
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("session_audio")}
        assert set(columns) == {"id", "session_log_id", "file_path", "duration_seconds", "created_at"}, columns
        for name in columns.keys() - {"id"}:
            assert columns[name]["nullable"] is False, name
        fks = inspect(conn).get_foreign_keys("session_audio")
        assert [f["referred_table"] for f in fks] == ["session_log"], fks

        with Operations.context(ctx):
            downgrade()
        assert "session_audio" not in inspect(conn).get_table_names()

    print("0009_create_session_audio_table self-check passed")
