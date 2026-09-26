"""Unit tests for GenerationService's prompt templates.

GAP 2 (Tri-Nature gap analysis, 2026-08-29): the explanation and grounding
judge prompt templates moved out of _build_prompt()/_build_judge_prompt() as
Python string literals into plain text files under rag/data/prompts/,
loaded once at import time and filled in with str.format(). These tests
pin that the extraction didn't change the interpolated output.
"""

from rag.services.foundations.generation.generation_service import GenerationService


class TestGenerationServicePromptLoading:

    def test_should_build_explanation_prompt_from_data_file_with_flag_and_chunk_interpolated(
        self, service, flag, chunk, other_chunk, chunks
    ):
        # when
        prompt = GenerationService._build_prompt(service, flag, chunks)

        # then
        assert repr(flag.said) in prompt
        assert repr(flag.corrected) in prompt
        assert flag.category in prompt
        assert chunk.content in prompt
        assert other_chunk.content in prompt

    def test_should_build_judge_prompt_from_data_file_with_explanation_and_chunk_interpolated(
        self, service, chunk, other_chunk, chunks
    ):
        # when
        prompt = GenerationService._build_judge_prompt(service, "a draft explanation", chunks)

        # then
        assert "a draft explanation" in prompt
        assert chunk.content in prompt
        assert other_chunk.content in prompt
        assert "YES" in prompt and "NO" in prompt
