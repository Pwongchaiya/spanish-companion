"""Chunk storage broker — the only read/write path to the `chunks` table.

Owns the SQLAlchemy engine and the pgvector cosine-distance search. No
business logic, no exception handling: raw SQLAlchemy/pgvector exceptions
propagate to the caller (Ingestion/Retrieval services map them per the
exception-hierarchy skill).
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from rag.models.retrieval import ScoredChunk

EMBEDDING_DIM = 384


class Base(DeclarativeBase):
    pass


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    source_url: Mapped[str]
    content: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    embedding_model_version: Mapped[str]
    chunking_strategy_version: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class SqlAlchemyChunkRepositoryBroker:
    """SQLAlchemy-backed implementation of ChunkRepositoryBroker."""

    def __init__(self, connection_string: str):
        # pg8000 (the only driver in requirements.txt) needs an explicit
        # "+pg8000" scheme -- a bare "postgresql://" (the standard format,
        # e.g. what a managed Postgres host hands back) resolves to the
        # psycopg2 dialect, which isn't installed. Same normalization as
        # alembic/env.py, applied here too since this is the one place the
        # running app (not just migrations) builds its engine.
        if connection_string.startswith("postgresql://"):
            connection_string = connection_string.replace("postgresql://", "postgresql+pg8000://", 1)
        self._engine = create_engine(connection_string)

    def insert_chunk(
        self,
        topic: str,
        source_url: str,
        content: str,
        embedding: list[float],
        embedding_model_version: str,
        chunking_strategy_version: str,
    ) -> int:
        chunk = Chunk(
            topic=topic,
            source_url=source_url,
            content=content,
            embedding=embedding,
            embedding_model_version=embedding_model_version,
            chunking_strategy_version=chunking_strategy_version,
        )
        with Session(self._engine) as session:
            session.add(chunk)
            session.commit()
            session.refresh(chunk)
            return chunk.id

    def search_by_vector(self, embedding: list[float], top_k: int) -> list[ScoredChunk]:
        distance = Chunk.embedding.cosine_distance(embedding).label("score")
        statement = select(Chunk, distance).order_by(distance).limit(top_k)
        with Session(self._engine) as session:
            rows = session.execute(statement).all()
        return [
            ScoredChunk(
                chunk_id=chunk.id,
                topic=chunk.topic,
                source_url=chunk.source_url,
                content=chunk.content,
                score=score,
                embedding_model_version=chunk.embedding_model_version,
                chunking_strategy_version=chunk.chunking_strategy_version,
            )
            for chunk, score in rows
        ]
