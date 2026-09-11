"""create learner_profile, mistake_pattern, topic_covered tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-10

Owned by the LearnerProfile Broker task (Wave 1) even though it only builds
LearnerProfile's model/broker code — MistakePattern and TopicCovered's
Broker Agents run after this migration lands and write code against tables
that must already exist in migration history. FK ordering requires all
three in one migration: mistake_pattern.profile_id and
topic_covered.profile_id both reference learner_profile.id.

Column definitions pulled from the entity docs (Obsidian
Projects/spanish-companion/entities/{learner-profile,mistake-pattern,
topic-covered}.md), not invented — see those docs for the dataclass shapes
this mirrors.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learner_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proficiency_level", sa.String(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "mistake_pattern",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("learner_profile.id"),
            nullable=False,
        ),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(),
            server_default="active",
            nullable=False,
        ),
        sa.UniqueConstraint("profile_id", "category", name="uq_mistake_pattern_profile_category"),
    )

    op.create_table(
        "topic_covered",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("learner_profile.id"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column(
            "first_covered_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_practiced_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("profile_id", "topic", name="uq_topic_covered_profile_topic"),
    )


def downgrade() -> None:
    # Reverse FK order: children before the parent they reference.
    op.drop_table("topic_covered")
    op.drop_table("mistake_pattern")
    op.drop_table("learner_profile")


if __name__ == "__main__":
    # ponytail: self-check that upgrade()/downgrade() are valid DDL with
    # correct FK ordering — runs them for real against an in-memory sqlite
    # engine via Alembic's Operations.context, not a live Postgres (no
    # broker-tier tests in this project, see CLAUDE.md / test-broker-skill).
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from sqlalchemy import create_engine, inspect

    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            upgrade()

        tables = set(inspect(conn).get_table_names())
        assert tables == {"learner_profile", "mistake_pattern", "topic_covered"}, tables

        fk_targets = {
            t: {fk["referred_table"] for fk in inspect(conn).get_foreign_keys(t)}
            for t in ("mistake_pattern", "topic_covered")
        }
        assert fk_targets["mistake_pattern"] == {"learner_profile"}
        assert fk_targets["topic_covered"] == {"learner_profile"}

        with Operations.context(ctx):
            downgrade()
        assert inspect(conn).get_table_names() == []

    print("0002_create_learner_profile_tables self-check passed")
