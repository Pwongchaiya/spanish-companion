"""create chunks table

Revision ID: 0001
Revises:
Create Date: 2026-08-29

Phase 1's rag/db.py:init_schema created a 5-column `chunks` table via raw
DDL (missing embedding_model_version and chunking_strategy_version). Per
user decision this migration drops and recreates rather than migrating in
place — backfilling version columns for pre-existing rows would be
fabricated data. The corpus is re-ingested from scratch once IngestionService
exists (later wave, not this migration's concern).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Drop Phase 1's raw-DDL chunks table (5 columns, no version tracking)
    # instead of adding columns — see module docstring.
    op.execute("DROP TABLE IF EXISTS chunks")

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("embedding_model_version", sa.String(), nullable=False),
        sa.Column("chunking_strategy_version", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.execute(
        "CREATE INDEX chunks_embedding_idx ON chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS chunks_embedding_idx")
    op.drop_table("chunks")
