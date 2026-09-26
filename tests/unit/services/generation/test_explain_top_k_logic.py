"""Unit tests for GenerationService.explain()'s #64 EXPLAIN_TOP_K slicing.

explain() now takes the caller's full retrieved (best-first) chunk list and
grounds only on the first EXPLAIN_TOP_K of them -- both the draft prompt and
the grounding judge prompt see the same slice. source_url/source_excerpt
always reflect chunks[0] (the top-ranked chunk), regardless of how many
chunks fed the prompt.
"""

from rag.models.orchestrations.retrieval import ScoredChunk
from rag.services.foundations.generation import GenerationService

from tests.unit.services.generation.conftest import FakeConfigurationBroker


def _chunk(chunk_id: int) -> ScoredChunk:
    return ScoredChunk(
        chunk_id=chunk_id,
        topic="preterite_vs_imperfect",
        source_url=f"https://rae.es/topic-{chunk_id}",
        content=f"contenido del fragmento numero {chunk_id}",
        score=1.0 / chunk_id,
    )


class TestGenerationServiceExplainTopK:

    def test_should_only_ground_on_first_explain_top_k_chunks_when_more_are_retrieved(
        self, mock_broker, mock_logging_broker, flag
    ):
        # given -- EXPLAIN_TOP_K=2, but 4 chunks retrieved
        service = GenerationService(
            broker=mock_broker,
            logging_broker=mock_logging_broker,
            configuration_broker=FakeConfigurationBroker({"EXPLAIN_TOP_K": "2"}),
        )
        chunks = [_chunk(1), _chunk(2), _chunk(3), _chunk(4)]
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunks)

        # then -- only the first two chunks' content reach either prompt
        (draft_prompt,), _ = mock_broker.generate.call_args_list[0]
        (judge_prompt,), _ = mock_broker.generate.call_args_list[1]
        assert chunks[0].content in draft_prompt and chunks[0].content in judge_prompt
        assert chunks[1].content in draft_prompt and chunks[1].content in judge_prompt
        assert chunks[2].content not in draft_prompt and chunks[2].content not in judge_prompt
        assert chunks[3].content not in draft_prompt and chunks[3].content not in judge_prompt

    def test_should_use_all_retrieved_chunks_when_fewer_than_explain_top_k(
        self, mock_broker, mock_logging_broker, flag
    ):
        # given -- EXPLAIN_TOP_K=5, only 2 chunks retrieved -- slicing a
        # 2-element list to [:5] returns the same 2 elements, no error.
        service = GenerationService(
            broker=mock_broker,
            logging_broker=mock_logging_broker,
            configuration_broker=FakeConfigurationBroker({"EXPLAIN_TOP_K": "5"}),
        )
        chunks = [_chunk(1), _chunk(2)]
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        service.explain(flag, chunks)

        # then
        (draft_prompt,), _ = mock_broker.generate.call_args_list[0]
        assert chunks[0].content in draft_prompt
        assert chunks[1].content in draft_prompt

    def test_should_return_top_ranked_chunk_source_regardless_of_explain_top_k(
        self, mock_broker, mock_logging_broker, flag
    ):
        # given
        service = GenerationService(
            broker=mock_broker,
            logging_broker=mock_logging_broker,
            configuration_broker=FakeConfigurationBroker({"EXPLAIN_TOP_K": "2"}),
        )
        chunks = [_chunk(1), _chunk(2), _chunk(3)]
        mock_broker.generate.side_effect = ["some explanation", "YES"]

        # when
        result = service.explain(flag, chunks)

        # then -- chunks[0] wins the single source_url/source_excerpt string,
        # never chunks[1] even though it also fed the prompt.
        assert result.source_url == chunks[0].source_url
        assert result.source_excerpt == chunks[0].content
