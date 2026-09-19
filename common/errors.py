"""Shared base for api- and rag-layer exception hierarchies.

Lets each package's Exposer/entrypoint catch one type instead of enumerating
every feature's exception class, without api and rag inheriting from each
other's error module (api -> rag is the only allowed direction).
"""

from typing import Optional


class BaseError(Exception):
    """Base for exceptions raised within either package.

    Optionally carries `inner_exception`, matching NL.Core.Entitlements'
    Xeption(message, innerException) base
    (NL.Core.Entitlements.Api/Models/Foundations/Entitlements/Exceptions/
    EntitlementValidationException.cs:11-13) -- wrapper-tier exceptions set
    this to the leaf exception they're wrapping; leaf exceptions leave it
    None.
    """

    def __init__(self, message: str, inner_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.inner_exception = inner_exception


if __name__ == "__main__":
    # ponytail: assert-based self-check -- confirms message propagation and
    # the inner_exception default/override, the two behaviors a broken edit
    # here would silently flip for every subclass in both packages.
    leaf = BaseError("boom")
    assert str(leaf) == "boom"
    assert leaf.inner_exception is None
    cause = ValueError("cause")
    wrapper = BaseError("wrapped", inner_exception=cause)
    assert wrapper.inner_exception is cause
    print("ok")
