"""create pronunciation_result table

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-19

Phase 4 B5 storage. Column shape is the one the user signed off on:
    pronunciation_result(id, created_at, reference_text, accuracy_score,
    fluency_score, completeness_score, pronunciation_score, prosody_score,
    words_json, locale)
`prosody_score` is nullable (Azure returns it for only some locales).
No audio is stored. No foreign key to learner_profile -- single-user
project, same reasoning as 0003_create_session_log_table.py.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pronunciation_result",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("reference_text", sa.String(), nullable=False),
        sa.Column("accuracy_score", sa.Float(), nullable=False),
        sa.Column("fluency_score", sa.Float(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("pronunciation_score", sa.Float(), nullable=False),
        sa.Column("prosody_score", sa.Float(), nullable=True),
        sa.Column("words_json", sa.JSON(), nullable=False),
        sa.Column("locale", sa.String(), server_default="es-ES", nullable=False),
    )
    op.create_index("ix_pronunciation_result_created_at", "pronunciation_result", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_pronunciation_result_created_at", table_name="pronunciation_result")
    op.drop_table("pronunciation_result")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0003 -- runs the real DDL
    # so a malformed column type fails here rather than against live Postgres.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        assert "pronunciation_result" in inspect(conn).get_table_names()
        columns = {c["name"]: c for c in inspect(conn).get_columns("pronunciation_result")}
        assert set(columns) == {
            "id",
            "created_at",
            "reference_text",
            "accuracy_score",
            "fluency_score",
            "completeness_score",
            "pronunciation_score",
            "prosody_score",
            "words_json",
            "locale",
        }, columns
        assert columns["prosody_score"]["nullable"] is True
        for name in columns.keys() - {"prosody_score", "id"}:
            assert columns[name]["nullable"] is False, name
        indexes = {i["name"]: i for i in inspect(conn).get_indexes("pronunciation_result")}
        assert indexes["ix_pronunciation_result_created_at"]["column_names"] == ["created_at"], indexes

        with Operations.context(ctx):
            downgrade()
        assert inspect(conn).get_table_names() == []
