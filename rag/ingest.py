"""RAE grammar corpus ingestion pipeline.

Fetches and chunks RAE grammar pages, generates embeddings, and stores in pgvector.
"""

import os

import numpy as np
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from sentence_transformers import SentenceTransformer

from rag.db import get_connection, init_schema, insert_chunk

load_dotenv()

# Configuration constants from environment variables
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
# BAAI/bge-small-en-v1.5 is English-only and can't meaningfully embed the
# Spanish corpus/queries this app actually uses (verified: every Spanish
# query collapsed onto the same topic) — multilingual model instead, same
# 384-dim output so the VECTOR(384) schema doesn't need to change.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# RAE grammar topics and their corresponding URLs
TOPICS: list[tuple[str, str]] = [
    (
        "preterite-vs-imperfect",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-indicativo/el-pret%C3%A9rito-perfecto-simple-cant%C3%A9-la-oposici%C3%B3n-cant%C3%A9-he-cantado",  # noqa: E501
    ),
    (
        "preterite-vs-imperfect",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-indicativo/el-pret%C3%A9rito-imperfecto-cantaba-la-oposici%C3%B3n-cant%C3%A9-cantaba",  # noqa: E501
    ),
    (
        "ser-vs-estar",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-atributo/el-atributo-en-las-oraciones-copulativas/atributos-con-ser-y-estar",  # noqa: E501
    ),
    (
        "subjunctive-basics",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/modo-y-subordinaci%C3%B3n/introducci%C3%B3n",
    ),
    (
        "subjunctive-basics",
        "https://www.rae.es/gram%C3%A1tica-b%C3%A1sica/el-verbo/tiempos-verbales-del-modo-subjuntivo/caracter%C3%ADsticas-generales",  # noqa: E501
    ),
]

# Module-level embedding model cache
_embedding_model: SentenceTransformer | None = None


def fetch_page_text(url: str) -> str:
    """Fetch and extract text content from a RAE grammar page.

    Args:
        url: The URL to fetch.

    Returns:
        Extracted visible text from the main content area.

    Raises:
        requests.RequestException: If the fetch fails.
        requests.HTTPError: If the response status is not 200.
    """
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove navigation, header, footer, script, and style tags
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Try to find main content area in order of preference
    content = soup.find("main")
    if content is None:
        content = soup.find("article")
    if content is None:
        content = soup.body

    if content is None:
        # Fallback: use entire soup if no body found
        content = soup

    # Extract text and collapse excess whitespace
    text = content.get_text()
    # Replace multiple newlines with single newline
    text = "\n".join(line for line in text.split("\n") if line.strip())
    # Replace multiple spaces with single space
    lines = text.split("\n")
    lines = [" ".join(line.split()) for line in lines]
    text = "\n".join(lines)

    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Split text into fixed-size chunks without overlap.

    Args:
        text: The text to chunk.

    Returns:
        List of text chunks, each of size up to CHUNK_SIZE characters.
    """
    chunks: list[str] = []
    for i in range(0, len(text), CHUNK_SIZE):
        chunk = text[i : i + CHUNK_SIZE].strip()
        if chunk:  # Skip empty or whitespace-only chunks
            chunks.append(chunk)
    return chunks


def embed_chunks(chunks: list[str]) -> np.ndarray:
    """Generate embeddings for a list of text chunks.

    Args:
        chunks: List of text chunks to embed.

    Returns:
        2D numpy array of embedding vectors (each row is a vector).
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(
            f"Loading embedding model: {EMBEDDING_MODEL_NAME}"
        )
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    embeddings = _embedding_model.encode(chunks, convert_to_tensor=False)
    return embeddings


def ingest_all() -> None:
    """Ingest all RAE grammar topics into the vector database.

    Fetches pages, chunks content, generates embeddings, and stores in pgvector.
    Continues on fetch failures but fails on chunking/embedding/DB errors.
    """
    conn = get_connection()
    init_schema(conn)

    try:
        for topic, url in TOPICS:
            try:
                logger.info(f"Fetching {topic} from {url}")
                text = fetch_page_text(url)
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
                continue

            # Chunk, embed, and insert (no try/except for these steps)
            chunks = chunk_text(text)
            embeddings = embed_chunks(chunks)

            for chunk, embedding in zip(chunks, embeddings):
                insert_chunk(conn, topic, url, chunk, embedding)

            logger.info(
                f"Inserted {len(chunks)} chunks for {topic} from {url}"
            )
    finally:
        conn.close()


if __name__ == "__main__":
    ingest_all()
