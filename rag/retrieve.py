"""Retrieve embeddings from the chunks table using pgvector."""

import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from loguru import logger

from rag.db import get_connection

load_dotenv()

# Must match rag/ingest.py's default exactly — see that file's comment for
# why this is multilingual rather than BGE-small-en.
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Load model once at module level
_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


# ponytail: with only 3 topics / ~30 chunks of dense RAE prose, top-1 cosine
# retrieval on a short Spanish example sentence (Review Mode's real query —
# the flag's "corrected" field) doesn't reliably hit the right topic, even
# though the scope doc's own named manual check (an English topic label like
# "preterite vs imperfect") passes reliably. Accepted per scope doc's explicit
# MVP exclusions (no query rewriting, no post-retrieval relevance filtering) —
# not a bug to chase now. Revisit at Step 6 reassessment if Review Mode
# explanations feel wrong in practice; likely fixes are a bigger/denser corpus
# or reranking, both explicitly out of scope for this pass.
def retrieve(query: str) -> dict[str, str] | None:
    """
    Embed the query and find the top-1 nearest neighbor in the chunks table.

    Args:
        query: The search query string.

    Returns:
        A dict with keys "topic", "source_url", "content" for the top match,
        or None if the table has no rows.
    """
    logger.debug(f"Retrieving for query: {query}")

    # Embed the query
    query_embedding = _model.encode(query)

    # Query the database
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT topic, source_url, content FROM chunks ORDER BY"
            " embedding <=> %s LIMIT 1",
            (query_embedding,),
        )

        row = cur.fetchone()

        if row is None:
            logger.debug("No chunks found in database")
            return None

        topic, source_url, content = row
        result = {"topic": topic, "source_url": source_url, "content": content}
        logger.debug(f"Retrieved topic: {topic}")
        return result

    finally:
        cur.close()
        conn.close()
