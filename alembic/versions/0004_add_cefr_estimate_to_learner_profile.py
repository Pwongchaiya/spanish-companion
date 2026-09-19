"""add cefr_estimate to learner_profile

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-18

Backs roadmap item A6 (async CEFR estimate from a session transcript).
`cefr_estimate` is nullable and distinct from the existing `proficiency_level`
column -- same nullable-String shape (see 0002_create_learner_profile_tables.py),
set independently by GenerationService.estimate_cefr_level() rather than by
the user/onboarding flow that sets proficiency_level.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("learner_profile", sa.Column("cefr_estimate", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("learner_profile", "cefr_estimate")


if __name__ == "__main__":
    # ponytail: same in-memory-sqlite self-check as 0002/0003 -- runs the
    # real DDL rather than asserting on the op.* call args.
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            op.create_table(
                "learner_profile",
                sa.Column("id", sa.Integer(), primary_key=True),
                sa.Column("proficiency_level", sa.String(), nullable=True),
            )
            upgrade()

        columns = {c["name"]: c for c in inspect(conn).get_columns("learner_profile")}
        assert "cefr_estimate" in columns, columns
        assert columns["cefr_estimate"]["nullable"] is True

        with Operations.context(ctx):
            downgrade()
        columns_after = {c["name"] for c in inspect(conn).get_columns("learner_profile")}
        assert "cefr_estimate" not in columns_after

    print("0004_add_cefr_estimate_to_learner_profile self-check passed")
