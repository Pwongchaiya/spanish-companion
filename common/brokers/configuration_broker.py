"""EnvConfigurationBroker — `os.environ`-backed ConfigurationBroker.

Shared by api/brokers/configuration and rag/brokers/configuration: same
concrete implementation, same env source, one copy instead of two
byte-for-byte twins. Each package's own `ConfigurationBroker` Protocol stays
local (api -> rag is the only allowed dependency direction; this common
module depends on neither).
"""

import os

from dotenv import load_dotenv


class EnvConfigurationBroker:
    """ConfigurationBroker backed by `os.environ`, loaded via `python-dotenv`."""

    def __init__(self) -> None:
        load_dotenv()

    def get(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    def require(self, key: str) -> str:
        return os.environ[key]


if __name__ == "__main__":
    # ponytail: assert-based self-check, no framework -- confirms default
    # fallback and required-key KeyError propagation, the two behaviors a
    # broken edit here would silently flip.
    os.environ["_CONFIG_BROKER_SELFTEST_KEY"] = "value"
    broker = EnvConfigurationBroker()
    assert broker.get("_CONFIG_BROKER_SELFTEST_KEY") == "value"
    assert broker.get("_CONFIG_BROKER_MISSING_KEY") is None
    assert broker.get("_CONFIG_BROKER_MISSING_KEY", "fallback") == "fallback"
    assert broker.require("_CONFIG_BROKER_SELFTEST_KEY") == "value"
    try:
        broker.require("_CONFIG_BROKER_MISSING_KEY")
        raise AssertionError("require() should have raised KeyError")
    except KeyError:
        pass
    del os.environ["_CONFIG_BROKER_SELFTEST_KEY"]
    print("OK")
