import os

import numpy as np
import psycopg
import pgvector.psycopg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str | None = os.getenv("DATABASE_URL")


def get_connection() -> psycopg.Connection:
    """Open a connection to the database and register pgvector adapter."""
    conn = psycopg.connect(DATABASE_URL)
    pgvector.psycopg.register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    """Create the vector extension, chunks table, and HNSW index if they don't exist."""
    ddl = """
    CREATE EXTENSION IF NOT EXISTS vector;

    CREATE TABLE IF NOT EXISTS chunks (
        id SERIAL PRIMARY KEY,
        topic TEXT NOT NULL,
        source_url TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding VECTOR(384) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

    CREATE INDEX IF NOT EXISTS chunks_embedding_idx
        ON chunks USING hnsw (embedding vector_cosine_ops);
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def insert_chunk(
    conn: psycopg.Connection,
    topic: str,
    source_url: str,
    content: str,
    embedding: np.ndarray | list[float],
) -> None:
    """Insert a chunk into the database."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chunks (topic, source_url, content, embedding) VALUES (%s, %s, %s, %s)",
            (topic, source_url, content, embedding),
        )
    conn.commit()
