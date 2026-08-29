"""Flask UI for Spanish Learning Companion.

Provides web interface for:
1. Starting/stopping voice conversation loop
2. Viewing live transcript as it streams
3. Reviewing flagged errors and practicing corrections

This is a single-user local MVP—no authentication, sessions, or CSRF protection.
"""

import json
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

from flask import Flask, render_template, request
from loguru import logger

from review.review import explain_flag, load_latest_flags, record_practice

# Initialize Flask app
app = Flask(__name__, template_folder="templates")

# Module-level state: currently-running voice bot subprocess
_current_process: Optional[subprocess.Popen] = None

# Compute repo root once at module load
REPO_ROOT = Path(__file__).parent.parent


def get_transcript_path() -> Path:
    """Return path to live transcript JSONL file."""
    return REPO_ROOT / "voice" / "logs" / "live_transcript.jsonl"


def _start_voice_process() -> subprocess.Popen:
    """Launch voice bot subprocess with proper Windows signal handling.

    Returns:
        The Popen object for the launched subprocess.

    Raises:
        RuntimeError if subprocess launch fails.
    """
    try:
        # Windows-specific: CREATE_NEW_PROCESS_GROUP is required to later
        # send CTRL_BREAK_EVENT and trigger Python's finally cleanup.
        # Without it, there's no graceful stop path (only hard kill).
        proc = subprocess.Popen(
            [sys.executable, "-m", "voice.bot"],
            cwd=str(REPO_ROOT),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        logger.info(f"Voice bot subprocess launched (PID {proc.pid})")
        return proc
    except Exception as e:
        logger.error(f"Failed to launch voice bot: {e}")
        raise RuntimeError(f"Failed to launch voice bot: {e}") from e


def _stop_voice_process(proc: subprocess.Popen) -> bool:
    """Stop voice bot subprocess gracefully with timeout and fallback.

    Sends CTRL_BREAK_EVENT (Windows only, requires CREATE_NEW_PROCESS_GROUP).
    Waits up to 5 seconds for graceful shutdown. Falls back to terminate()
    if timeout occurs.

    Args:
        proc: The Popen object to stop.

    Returns:
        True if stopped gracefully, False if forced (fallback to terminate).
    """
    try:
        logger.info(f"Stopping voice bot (PID {proc.pid}) gracefully...")
        # Windows-specific signal: CTRL_BREAK_EVENT only works with CREATE_NEW_PROCESS_GROUP
        proc.send_signal(signal.CTRL_BREAK_EVENT)
        try:
            proc.wait(timeout=5)
            logger.info("Voice bot exited gracefully")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("Graceful shutdown timed out, force-terminating...")
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.error("Force terminate also timed out, killing...")
                proc.kill()
            return False
    except Exception as e:
        logger.error(f"Error stopping voice bot: {e}")
        return False


@app.route("/", methods=["GET"])
def index() -> str:
    """Render main page with Start/Stop buttons, transcript, and review link."""
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start() -> tuple[dict, int]:
    """Start voice conversation session.

    Returns:
        JSON response with success/error status.
    """
    global _current_process

    if _current_process is not None and _current_process.poll() is None:
        logger.warning("Attempted to start a new session while one is running")
        return {"error": "Session already running"}, 400

    try:
        _current_process = _start_voice_process()
        return {"status": "started"}, 200
    except RuntimeError as e:
        logger.error(f"Failed to start session: {e}")
        return {"error": str(e)}, 500


@app.route("/stop", methods=["POST"])
def stop() -> tuple[dict, int]:
    """Stop voice conversation session gracefully.

    Returns:
        JSON response with success/error status.
    """
    global _current_process

    if _current_process is None or _current_process.poll() is not None:
        logger.info("Attempted to stop session but none is running")
        return {"error": "No session running"}, 400

    graceful = _stop_voice_process(_current_process)
    _current_process = None

    return {
        "status": "stopped",
        "graceful": graceful,
    }, 200


@app.route("/transcript", methods=["GET"])
def transcript() -> tuple[dict, int]:
    """Stream live transcript from voice conversation.

    Reads voice/logs/live_transcript.jsonl line by line, skipping any
    unparseable lines to handle partial writes gracefully.

    Returns:
        JSON with "turns" list of transcript entries.
    """
    transcript_path = get_transcript_path()

    if not transcript_path.exists():
        return {"turns": []}, 200

    turns = []
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    turn = json.loads(line)
                    turns.append(turn)
                except json.JSONDecodeError:
                    # Skip unparseable lines (partial writes from active bot)
                    logger.debug(f"Skipped unparseable transcript line: {line[:50]}")
                    continue
    except IOError as e:
        logger.error(f"Error reading transcript file: {e}")
        return {"turns": []}, 500

    return {"turns": turns}, 200


@app.route("/review", methods=["GET"])
def review_list() -> str:
    """Render review page listing all flagged errors."""
    flags = load_latest_flags()
    return render_template("review.html", flags=flags, stage="list")


@app.route("/review/select", methods=["POST"])
def review_select() -> tuple[str, int]:
    """Load explanation for selected flag and render practice form.

    Args:
        flag_index: Index of flag in the latest_flags.json list.

    Returns:
        Rendered HTML page with explanation and practice form, or error page.
    """
    try:
        flag_index = int(request.form.get("flag_index", -1))
    except ValueError:
        logger.warning("Invalid flag_index in review_select")
        return render_template(
            "review.html",
            error="Invalid flag index",
            stage="error",
        ), 400

    flags = load_latest_flags()

    if not (0 <= flag_index < len(flags)):
        logger.warning(f"Flag index out of range: {flag_index}, total: {len(flags)}")
        return render_template(
            "review.html",
            error=f"Flag index out of range (0-{len(flags) - 1})",
            stage="error",
        ), 400

    selected_flag = flags[flag_index]

    # Retrieve explanation (this makes a Gemini API call, can take a few seconds)
    logger.info(f"Generating explanation for flag {flag_index}: {selected_flag['category']}")
    explanation_data = explain_flag(selected_flag)

    return render_template(
        "review.html",
        flag_index=flag_index,
        flag=selected_flag,
        explanation=explanation_data["explanation"],
        source_url=explanation_data["source_url"],
        stage="practice",
    ), 200


@app.route("/review/practice", methods=["POST"])
def review_practice() -> tuple[str, int]:
    """Record practice attempt and show confirmation.

    Args:
        flag_index: Index of the flag being practiced.
        attempt_text: User's typed practice attempt.

    Returns:
        Confirmation page or error.
    """
    try:
        flag_index = int(request.form.get("flag_index", -1))
        attempt_text = request.form.get("attempt_text", "").strip()
    except ValueError:
        logger.warning("Invalid form data in review_practice")
        return render_template(
            "review.html",
            error="Invalid form data",
            stage="error",
        ), 400

    flags = load_latest_flags()

    if not (0 <= flag_index < len(flags)):
        logger.warning(f"Flag index out of range in practice: {flag_index}")
        return render_template(
            "review.html",
            error=f"Flag index out of range",
            stage="error",
        ), 400

    if not attempt_text:
        logger.warning("Empty practice attempt")
        return render_template(
            "review.html",
            error="Please enter a practice attempt",
            stage="error",
        ), 400

    selected_flag = flags[flag_index]

    # Record the practice attempt (writes to review/logs/)
    try:
        record_practice(selected_flag, attempt_text)
        logger.info(f"Practice recorded for flag {flag_index}")
        return render_template(
            "review.html",
            stage="done",
        ), 200
    except Exception as e:
        logger.error(f"Failed to record practice: {e}")
        return render_template(
            "review.html",
            error="Failed to record practice.",
            stage="error",
        ), 500


@app.errorhandler(404)
def not_found(error) -> tuple[dict, int]:
    """Handle 404 errors gracefully."""
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def internal_error(error) -> tuple[dict, int]:
    """Handle 500 errors gracefully."""
    logger.error(f"Internal server error: {error}")
    return {"error": "Internal server error"}, 500


if __name__ == "__main__":
    # debug=False (not just use_reloader=False): this app tracks a running
    # subprocess in module-level state (_current_process). Debug mode's
    # reloader can respawn the serving process on its own — verified this
    # happens even with use_reloader explicitly set to False in this
    # environment — which silently orphans any running voice/bot.py
    # subprocess (no way left to send it CTRL_BREAK_EVENT, so its session
    # log/flags never get saved). Not worth debug mode's convenience for a
    # tool that manages real subprocess/hardware side effects.
    app.run(port=5000)
