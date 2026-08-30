"""Error-flag parsing for the live voice conversation.

The LLM appends <flag>{...}</flag> blocks to its reply per prompts.py's
instructions; this module turns matched blocks into validated flag dicts.
Split out of voice_conversation_service.py for single-responsibility.
"""

import json
from typing import Optional

from loguru import logger

FLAG_START = "<flag>"
FLAG_END = "</flag>"
FLAG_TYPE = "error_flag"
FLAG_KEYS = ("said", "corrected", "category")


def parse_flag(content: str) -> Optional[dict]:
    """Parse one <flag> block's JSON payload. Returns None (and warns) if the
    model emitted something unparseable — a dropped flag is fine, a crashed
    voice loop is not."""
    try:
        flag = json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Dropped unparseable error flag: {content!r}")
        return None
    if not isinstance(flag, dict) or not all(isinstance(flag.get(key), str) for key in FLAG_KEYS):
        logger.warning(f"Dropped malformed error flag: {content!r}")
        return None
    return {key: flag[key] for key in FLAG_KEYS}
