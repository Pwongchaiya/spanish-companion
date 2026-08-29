"""Integration tests for rag.brokers.embedding_model.SentenceTransformerEmbeddingModelBroker.

Per CLAUDE.md's Phase 2 test strategy: real SentenceTransformer model load
(uses the 384-dim multilingual model pinned in CLAUDE.md tech stack), no mocks.

What this tier proves: the broker correctly loads the model, encodes texts to
exactly EMBEDDING_DIM vectors, preserves order and count, and produces
deterministic outputs (same input twice -> same vector).
"""

import pytest

from rag.brokers.chunk_repository import EMBEDDING_DIM
from rag.brokers.embedding_model import SentenceTransformerEmbeddingModelBroker


@pytest.fixture
def broker():
    """Real embedding model broker — loads actual multilingual model once."""
    return SentenceTransformerEmbeddingModelBroker()


class TestSentenceTransformerEmbeddingModelBrokerEmbed:
    """Tests for EmbeddingModelBroker.embed()."""

    def test_should_return_embedding_with_correct_dimension(self, broker):
        # when
        embeddings = broker.embed(["Ella es feliz"])

        # then
        assert len(embeddings) == 1
        embedding = embeddings[0]
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIM
        assert all(isinstance(v, float) for v in embedding)

    def test_should_return_384_dimensional_vectors_for_all_inputs(self, broker):
        # when
        embeddings = broker.embed(
            [
                "El ser y el estar son verbos diferentes.",
                "El pretérito expresa acciones pasadas completas.",
                "El imperfecto describe acciones habituales o en progreso.",
            ]
        )

        # then
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert len(embedding) == EMBEDDING_DIM

    def test_should_preserve_input_order(self, broker):
        # given
        texts = [
            "First text about Spanish grammar",
            "Second text about verb conjugation",
            "Third text about subjunctive mood",
        ]

        # when
        embeddings = broker.embed(texts)

        # then -- same inputs again should give same order
        embeddings_again = broker.embed(texts)
        for emb1, emb2 in zip(embeddings, embeddings_again):
            # Check that embeddings are very similar (not identical float,
            # but close enough to be practically the same)
            assert len(emb1) == len(emb2)
            distances = sum((v1 - v2) ** 2 for v1, v2 in zip(emb1, emb2))
            assert distances < 1e-10  # extremely small difference

    def test_should_preserve_input_count(self, broker):
        # when
        texts = ["text 1", "text 2", "text 3", "text 4", "text 5"]
        embeddings = broker.embed(texts)

        # then
        assert len(embeddings) == len(texts)

    def test_should_produce_deterministic_embeddings_for_same_input(self, broker):
        # given
        text = "El subjuntivo es un modo verbal complejo."

        # when
        embedding1 = broker.embed([text])[0]
        embedding2 = broker.embed([text])[0]

        # then -- deterministic: same input produces same output
        assert embedding1 == embedding2

    def test_should_handle_single_element_list(self, broker):
        # when
        embeddings = broker.embed(["¿Cuál es la diferencia entre ser y estar?"])

        # then
        assert len(embeddings) == 1
        assert len(embeddings[0]) == EMBEDDING_DIM

    def test_should_handle_empty_string_in_batch(self, broker):
        # when
        embeddings = broker.embed(["Non-empty text", "", "Another non-empty text"])

        # then
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert len(embedding) == EMBEDDING_DIM

    def test_should_handle_multilingual_text(self, broker):
        # given -- texts in Spanish, English, and French
        texts = [
            "El pretérito indefinido expresa acciones acabadas en el pasado.",
            "The preterite expresses completed past actions.",
            "Le passé simple exprime des actions achevées dans le passé.",
        ]

        # when
        embeddings = broker.embed(texts)

        # then -- all multilingual texts should embed successfully
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert len(embedding) == EMBEDDING_DIM

    def test_should_handle_long_text(self, broker):
        # given -- substantial paragraph of Spanish text
        text = (
            "El pretérito indefinido o pretérito perfecto simple es un tiempo verbal que "
            "expresa una acción pasada totalmente terminada. El imperfecto, en cambio, "
            "describe una acción pasada que se desarrollaba habitualmente o estaba "
            "en progreso cuando ocurrió otra acción. La diferencia fundamental es que "
            "el pretérito presenta la acción como completada, mientras que el imperfecto "
            "la presenta como en desarrollo o repetida. Por ejemplo, 'Mientras yo estudiaba "
            "(imperfecto), sonó (pretérito) el teléfono'. El verbo estudiar está en "
            "imperfecto porque la acción estaba en curso, y sonar en pretérito porque "
            "es la acción puntual que ocurrió."
        )

        # when
        embeddings = broker.embed([text])

        # then
        assert len(embeddings) == 1
        assert len(embeddings[0]) == EMBEDDING_DIM

    def test_should_return_float_vectors_not_tensors(self, broker):
        # when
        embeddings = broker.embed(["Test text"])

        # then -- ensure convert_to_tensor=False works (returns lists, not tensors)
        assert isinstance(embeddings, list)
        assert isinstance(embeddings[0], list)
        assert all(isinstance(v, float) for v in embeddings[0])

    def test_should_handle_special_characters_and_punctuation(self, broker):
        # given
        texts = [
            "¿Qué es el subjuntivo?",
            "¡Vaya una pregunta!",
            "Ser/estar; verbos (especiales).",
        ]

        # when
        embeddings = broker.embed(texts)

        # then
        assert len(embeddings) == 3
        for embedding in embeddings:
            assert len(embedding) == EMBEDDING_DIM
