"""GeminiGenerationBroker — google-genai-backed GenerationBroker."""

import os
from types import SimpleNamespace
from typing import Optional

import google.genai as genai

from rag.brokers.generation.i_generation_broker import GenerationError

# Matches voice/bot.py's and review/review.py's existing default exactly —
# Gemini Flash-Lite, per CLAUDE.md tech stack.
_DEFAULT_MODEL_NAME = "gemini-flash-lite-latest"


class GeminiGenerationBroker:
    """GenerationBroker backed by google-genai's Gemini client.

    `api_key`/`model_name` default to GEMINI_API_KEY/GEMINI_MODEL (env),
    then the project's pinned Flash-Lite default — same defaulting shape as
    api/brokers/bot_process/bot_process_broker.py's `command`/`cwd`.

    # ponytail: broker-skill's "no try/except in a broker" default is
    # deliberately not followed here — the empty/None-response guard and
    # client-failure wrap into GenerationError are the explicit, only
    # exception this feature has (per CLAUDE.md's Foundation waiver for
    # Generation), and this is an external-dependency failure mode with
    # nowhere else to live given this project's 3-layer Broker/Service/
    # Controller architecture. A later GenerationService catches
    # GenerationError and substitutes a fallback string.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> None:
        resolved_api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self._model_name = model_name if model_name is not None else os.getenv("GEMINI_MODEL", _DEFAULT_MODEL_NAME)
        self._client = genai.Client(api_key=resolved_api_key)
        # #68: unset (None) keeps today's behavior -- no config passed, API's own
        # default temperature. Set only by evals/run_eval.py's judge broker so far.
        self._temperature = temperature

    def generate(self, prompt: str) -> str:
        config = (
            genai.types.GenerateContentConfig(temperature=self._temperature) if self._temperature is not None else None
        )
        try:
            response = self._client.models.generate_content(model=self._model_name, contents=prompt, config=config)
        except Exception as e:
            raise GenerationError(f"Gemini client call failed: {e}") from e

        # response.text can be None (e.g. safety-blocked/empty candidate)
        # even without raising — same behavior review/review.py guarded
        # against, now enforced as the broker's contract instead of left
        # to each caller.
        text = getattr(response, "text", None)
        if not text:
            raise GenerationError("Gemini returned an empty or None response")
        return text


def _self_test() -> None:
    """#68: temperature=None must not build a config; a real value must. No network,
    no broker test tier exists per project convention -- this is the smallest check
    that fails if the branch at generate()'s top regresses."""
    broker = object.__new__(GeminiGenerationBroker)
    captured = {}

    class _FakeModels:
        def generate_content(self, *, model, contents, config):
            captured["config"] = config
            return SimpleNamespace(text="ok")

    broker._client = SimpleNamespace(models=_FakeModels())
    broker._model_name = "test-model"

    broker._temperature = None
    broker.generate("hi")
    assert captured["config"] is None, "temperature=None must pass config=None (today's behavior)"

    broker._temperature = 0.0
    broker.generate("hi")
    assert (
        captured["config"] is not None and captured["config"].temperature == 0.0
    ), "temperature=0.0 must build a config"

    print("self-test ok")


if __name__ == "__main__":
    _self_test()
