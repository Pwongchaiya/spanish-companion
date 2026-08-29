"""Assert-based smoke tests for error-flag parsing and aggregation.

Tests the real PatternPairAggregator configured exactly as in bot.py,
feeding canned LLM replies through it in deliberately awkward chunks.
No test framework, no API keys/audio needed.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger
from pipecat.utils.text.pattern_pair_aggregator import (
    MatchAction,
    PatternMatch,
    PatternPairAggregator,
)

from bot import FLAG_END, FLAG_KEYS, FLAG_START, FLAG_TYPE, parse_flag


def test_parse_flag_invalid_json() -> None:
    """Assert parse_flag returns None for invalid JSON."""
    result = parse_flag("not json")
    assert result is None, f"Expected None, got {result!r}"


def test_parse_flag_wrong_type() -> None:
    """Assert parse_flag returns None when a required key has wrong type."""
    result = parse_flag('{"said": 1, "corrected": "test", "category": "test"}')
    assert result is None, f"Expected None for wrong type, got {result!r}"


def test_parse_flag_valid() -> None:
    """Assert parse_flag correctly parses valid flag JSON."""
    content = '{"said": "el gatos", "corrected": "los gatos", "category": "gender agreement"}'
    result = parse_flag(content)
    assert result is not None, "Expected valid parse result"
    assert result["said"] == "el gatos"
    assert result["corrected"] == "los gatos"
    assert result["category"] == "gender agreement"


async def test_aggregator_with_split_chunks() -> None:
    """Feed a canned reply through the aggregator in deliberately awkward chunks.

    The aggregator is initialized with the exact same config as in bot.py.
    We feed chunks that split the flag marker and JSON payload mid-string to ensure
    robust buffering.
    """
    aggregator = PatternPairAggregator()
    aggregator.add_pattern(
        type=FLAG_TYPE,
        start_pattern=FLAG_START,
        end_pattern=FLAG_END,
        action=MatchAction.REMOVE,
    )

    collected_matches: list[PatternMatch] = []

    async def on_error_flag(match: PatternMatch) -> None:
        collected_matches.append(match)

    aggregator.on_pattern_match(FLAG_TYPE, on_error_flag)

    # Feed it in deliberately awkward chunks:
    # Split across the <fl / ag> boundary and mid-JSON payload
    chunks = [
        "Great! Now, can you count to ten? <fl",
        'ag>{"said": "tengo 25", "corrected"',
        ': "tengo veinticinco", "category": "numbers"}</flag>',
    ]

    spoken_text_parts: list[str] = []
    for chunk in chunks:
        async for match in aggregator.aggregate(chunk):
            if hasattr(match, "text"):
                spoken_text_parts.append(match.text)

    # Flush any remaining buffered text
    flushed = await aggregator.flush()
    if flushed and hasattr(flushed, "text"):
        spoken_text_parts.append(flushed.text)

    spoken_text = "".join(spoken_text_parts)

    # Assert the flag was removed from spoken text
    assert "<" not in spoken_text, f"Spoken text contains '<': {spoken_text!r}"
    assert "flag" not in spoken_text, f"Spoken text contains 'flag': {spoken_text!r}"
    assert "{" not in spoken_text, f"Spoken text contains '{{': {spoken_text!r}"
    # Check that key words from the message are present (space handling may vary by aggregator)
    assert (
        "count" in spoken_text and "ten" in spoken_text
    ), f"Spoken text lost the main message: {spoken_text!r}"

    # Assert the handler was called exactly once with correct data
    assert len(collected_matches) == 1, f"Expected 1 match, got {len(collected_matches)}"
    match = collected_matches[0]
    parsed = parse_flag(match.text)
    assert parsed is not None, f"Failed to parse captured flag text: {match.text!r}"
    assert parsed["said"] == "tengo 25"
    assert parsed["corrected"] == "tengo veinticinco"
    assert parsed["category"] == "numbers"


async def test_unclosed_flag_tag() -> None:
    """Assert a reply with an UNCLOSED <flag> tag produces spoken text
    with nothing from the tag onward."""
    aggregator = PatternPairAggregator()
    aggregator.add_pattern(
        type=FLAG_TYPE,
        start_pattern=FLAG_START,
        end_pattern=FLAG_END,
        action=MatchAction.REMOVE,
    )

    # Reply with unclosed flag tag
    reply = "You said something. <flag>{incomplete json"

    spoken_text_parts: list[str] = []
    async for match in aggregator.aggregate(reply):
        if hasattr(match, "text"):
            spoken_text_parts.append(match.text)

    flushed = await aggregator.flush()
    if flushed and hasattr(flushed, "text"):
        spoken_text_parts.append(flushed.text)

    spoken_text = "".join(spoken_text_parts)

    # The unclosed tag should be buffered; the prefix before the tag should survive,
    # but the tag content should not leak into spoken text.
    assert "You said something" in spoken_text, f"Prefix text missing from spoken output: {spoken_text!r}"
    assert "{" not in spoken_text, f"Unclosed flag leaked JSON to spoken text: {spoken_text!r}"
    assert "incomplete" not in spoken_text, f"Unclosed flag leaked content: {spoken_text!r}"


async def test_multiple_flags() -> None:
    """Assert multiple flag blocks in one reply are all captured."""
    aggregator = PatternPairAggregator()
    aggregator.add_pattern(
        type=FLAG_TYPE,
        start_pattern=FLAG_START,
        end_pattern=FLAG_END,
        action=MatchAction.REMOVE,
    )

    collected_matches: list[PatternMatch] = []

    async def on_error_flag(match: PatternMatch) -> None:
        collected_matches.append(match)

    aggregator.on_pattern_match(FLAG_TYPE, on_error_flag)

    flag1 = '{"said": "es bonita", "corrected": "está bonita", "category": "ser vs estar"}'
    flag2 = '{"said": "los libros", "corrected": "el libro", "category": "gender"}'
    reply = f"Nice try! {FLAG_START}{flag1}{FLAG_END} Also note: {FLAG_START}{flag2}{FLAG_END}"

    async for match in aggregator.aggregate(reply):
        pass

    flushed = await aggregator.flush()

    # Assert both flags were captured
    assert len(collected_matches) == 2, f"Expected 2 matches, got {len(collected_matches)}"

    # Verify both flags parse correctly
    for i, match in enumerate(collected_matches):
        parsed = parse_flag(match.text)
        assert parsed is not None, f"Match {i} failed to parse: {match.text!r}"
        assert all(key in parsed for key in FLAG_KEYS), f"Match {i} missing keys: {parsed!r}"


async def async_main() -> None:
    """Run all async tests."""
    logger.info("Running aggregator tests...")
    await test_aggregator_with_split_chunks()
    logger.info("✓ test_aggregator_with_split_chunks passed")

    await test_unclosed_flag_tag()
    logger.info("✓ test_unclosed_flag_tag passed")

    await test_multiple_flags()
    logger.info("✓ test_multiple_flags passed")


if __name__ == "__main__":
    try:
        logger.info("Running parse_flag tests...")
        test_parse_flag_invalid_json()
        logger.info("✓ test_parse_flag_invalid_json passed")

        test_parse_flag_wrong_type()
        logger.info("✓ test_parse_flag_wrong_type passed")

        test_parse_flag_valid()
        logger.info("✓ test_parse_flag_valid passed")

        asyncio.run(async_main())

        logger.info("All flag tests passed!")
    except AssertionError as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
