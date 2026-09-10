"""Broker for environment configuration.

Wraps `os.environ`/`python-dotenv` so Foundation/Orchestration services can
read config without reading the environment directly themselves — the same
seam `Brokers/Configurations/IConfigurationBroker.cs` plays in the reference
project (`NL.Core.Users.Api`), consumed from both its Foundation and
Orchestration tiers. Reading env vars at import time (the H1 audit finding
this broker fixes) makes config impossible to vary per test; a constructor-
injected broker read inside `__init__`/methods fixes that.

Local to `rag`, not imported from `api.brokers.configuration`: `rag` must
never import from `api` (one-directional dependency: api -> rag). This is
the rag-side twin of `api/brokers/configuration/i_configuration_broker.py` —
structurally identical, so `api.brokers.configuration.EnvConfigurationBroker`
satisfies this Protocol too and can be injected directly from `api/app.py`'s
composition root when a caller wants every service (api- and rag-side) to
share one config source.

Only `get`/`require` are defined — no typed getters (int/float/Path). Casting
stays at each call site, deliberately: this broker's job is sourcing a raw
string, not validating its shape.

No flow control, no exception handling, no business logic — this broker only
wraps `os.environ` access.
"""

from typing import Protocol


class ConfigurationBroker(Protocol):
    """External-resource boundary for environment configuration."""

    def get(self, key: str, default: str | None = None) -> str | None:
        """Return `key`'s value, or `default` if unset."""
        ...

    def require(self, key: str) -> str:
        """Return `key`'s value. Raises `KeyError` if unset."""
        ...
