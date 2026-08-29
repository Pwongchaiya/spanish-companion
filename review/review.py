"""Review Mode: load flagged errors from live conversation, retrieve RAG-grounded
explanations, and record practice attempts.

This module exposes three functions for integration with a web layer:
- load_latest_flags(): read flags from voice/logs/latest_flags.json
- explain_flag(flag): retrieve RAE grammar content, generate explanation via Gemini
- record_practice(flag, attempt_text): log the practice attempt

All three functions are untimed; no real-time constraints. Explanation generation
uses non-streaming Gemini calls since this is a text-based review screen.

The __main__ block provides a standalone interactive CLI for testing.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import google.genai as genai
from dotenv import load_dotenv
from loguru import logger

from rag.retrieve import retrieve

# Load .env at module import time, per project pattern (voice/bot.py)
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")


def load_latest_flags() -> list[dict[str, str]]:
    """Load flagged grammar errors from voice/logs/latest_flags.json.

    Returns:
        A list of flag dicts, each with "said", "corrected", "category" keys.
        Returns an empty list if the file doesn't exist.
    """
    flags_path = Path(__file__).parent.parent / "voice" / "logs" / "latest_flags.json"

    if not flags_path.exists():
        logger.debug(f"No flags file found at {flags_path}")
        return []

    try:
        # Handle UTF-8 BOM that some tools (e.g. PowerShell) may add
        content = flags_path.read_text(encoding="utf-8-sig")
        flags = json.loads(content)
        if not isinstance(flags, list):
            logger.warning(f"Flags file contains non-list JSON: {type(flags)}")
            return []
        logger.debug(f"Loaded {len(flags)} flags from {flags_path}")
        return flags
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to read flags file {flags_path}: {e}")
        return []


def explain_flag(flag: dict[str, str]) -> dict[str, str]:
    """Generate a RAG-grounded explanation of a flagged grammar correction.

    Retrieves the top-matching RAE grammar chunk for the corrected form,
    then asks Gemini to write a warm, encouraging explanation of the
    correction grounded in that content.

    Args:
        flag: A dict with "said", "corrected", "category" keys.

    Returns:
        A dict with "explanation" and "source_url" keys.
        If no corpus match is found, returns a fixed fallback response.
    """
    query = flag["corrected"]
    logger.debug(f"Explaining flag: {flag['category']}, query={query!r}")

    # Retrieve grammar chunk for the corrected form
    retrieved = retrieve(query)

    if retrieved is None:
        logger.debug(f"No retrieval result for query {query!r}, using fallback")
        return {"explanation": "I'm not certain on that one.", "source_url": ""}

    # Build prompt for Gemini explanation
    prompt = (
        f"A Spanish learner made this grammar mistake:\n"
        f"- They said: {flag['said']!r}\n"
        f"- They meant: {flag['corrected']!r}\n"
        f"- Category: {flag['category']}\n\n"
        f"Here is relevant grammar content from the RAE (Royal Spanish Academy):\n"
        f"{retrieved['content']}\n\n"
        f"Write a short, warm, encouraging explanation (2-3 sentences) of the "
        f"correction, grounded in the grammar content above. Explain why the "
        f"corrected form is right and what the learner confused. Keep it friendly "
        f"and supportive, suitable for display as text on a review screen."
    )

    # Generate explanation via Gemini (non-streaming, one-shot call)
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        # response.text can be None (e.g. safety-blocked/empty candidate) even
        # without raising — guard so we never violate our own dict[str, str] contract.
        explanation = response.text or "I'm not certain on that one."
        logger.debug(f"Generated explanation for {flag['category']}")
        return {"explanation": explanation, "source_url": retrieved["source_url"]}

    except Exception as e:
        logger.error(f"Failed to generate explanation via Gemini: {e}")
        return {
            "explanation": "I'm not certain on that one.",
            "source_url": retrieved.get("source_url", ""),
        }


def record_practice(flag: dict[str, str], attempt_text: str) -> None:
    """Record a practice attempt for a flagged error.

    Writes a simple timestamped log file under review/logs/ with the flag
    details and the user's typed practice attempt. No grading or correctness
    checking — just record it for later review.

    Args:
        flag: A dict with "said", "corrected", "category" keys.
        attempt_text: The user's typed practice attempt.
    """
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    log_path = log_dir / f"{timestamp}.log"

    output_lines = [
        f"Category: {flag['category']}",
        f"Originally said: {flag['said']}",
        f"Correct form: {flag['corrected']}",
        f"Practice attempt: {attempt_text}",
    ]

    log_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
    logger.debug(f"Recorded practice attempt to {log_path}")


if __name__ == "__main__":
    # Interactive CLI for testing Review Mode
    flags = load_latest_flags()

    if not flags:
        print("No flagged errors found. Run a voice conversation first.")
        exit(0)

    print(f"\nFound {len(flags)} flagged errors:")
    print("-" * 60)

    for i, flag in enumerate(flags, 1):
        print(f"{i}. [{flag['category']}] said: {flag['said']!r} -> {flag['corrected']!r}")

    print()

    # User picks a flag
    while True:
        try:
            choice = input("Pick a flag to review (number): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(flags):
                selected_flag = flags[idx]
                break
            else:
                print(f"Please enter a number between 1 and {len(flags)}.")
        except ValueError:
            print(f"Please enter a valid number between 1 and {len(flags)}.")

    print("\n" + "=" * 60)
    print(f"Reviewing: [{selected_flag['category']}]")
    print(f"You said: {selected_flag['said']!r}")
    print(f"Correct: {selected_flag['corrected']!r}")
    print("=" * 60)

    # Get explanation
    result = explain_flag(selected_flag)
    print(f"\nExplanation:\n{result['explanation']}")
    if result["source_url"]:
        print(f"\nSource: {result['source_url']}")

    # Practice attempt
    print()
    practice_text = input("Try saying the corrected form (type it): ").strip()

    if practice_text:
        record_practice(selected_flag, practice_text)
        print("Practice recorded. Well done!")
    else:
        print("Skipped practice.")
