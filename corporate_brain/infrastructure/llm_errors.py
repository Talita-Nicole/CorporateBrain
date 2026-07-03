"""Typed LLM provider errors, raised by adapters instead of raw SDK exceptions."""

import logging
from contextlib import contextmanager
from typing import Iterator

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# APITimeoutError is not guaranteed to subclass APIConnectionError across
# openai SDK versions, so it is listed explicitly rather than relying on
# APIConnectionError to catch it.
LLM_SDK_ERRORS = (AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError)


class LLMServiceError(Exception):
    """Configuration/setup error carrying a user-facing message.

    Used for errors known statically before any SDK call is made (unknown
    provider, missing configuration) — the message is already appropriate
    to show as-is, unlike ``LLMCallError``.
    """


class LLMCallError(Exception):
    """Base class for errors translated from an LLM provider SDK call.

    Carries structured context (``provider``, ``credential_hint``) instead of
    a pre-composed message — presentation code decides how to phrase it.
    """

    def __init__(self, *, provider: str, credential_hint: str) -> None:
        self.provider = provider
        self.credential_hint = credential_hint
        super().__init__(f"{type(self).__name__} for {provider}")


class LLMAuthError(LLMCallError):
    """Raised when the provider rejects the configured credentials."""


class LLMRateLimitError(LLMCallError):
    """Raised when the provider's request rate limit is exceeded."""


class LLMTimeoutError(LLMCallError):
    """Raised when a call to the provider times out."""


class LLMConnectionError(LLMCallError):
    """Raised when the provider endpoint cannot be reached."""


class LLMUnknownError(LLMCallError):
    """Raised for any other SDK error communicating with the provider."""


def _translate_llm_error(
    error: Exception, *, provider: str, credential_hint: str
) -> LLMCallError:
    """Map an LLM provider SDK error to a typed ``LLMCallError``."""
    kwargs = {"provider": provider, "credential_hint": credential_hint}
    if isinstance(error, AuthenticationError):
        typed = LLMAuthError(**kwargs)
    elif isinstance(error, RateLimitError):
        typed = LLMRateLimitError(**kwargs)
    elif isinstance(error, APITimeoutError):
        typed = LLMTimeoutError(**kwargs)
    elif isinstance(error, APIConnectionError):
        typed = LLMConnectionError(**kwargs)
    else:
        typed = LLMUnknownError(**kwargs)
    logger.error("%s error: %s", provider, error)
    return typed


@contextmanager
def with_llm_error_translation(provider: str, credential_hint: str) -> Iterator[None]:
    """Wrap an SDK call, re-raising known errors as a typed ``LLMCallError``.

    Shared by the embedder and language-model adapters so each one does not
    repeat the same ``try/except LLM_SDK_ERRORS`` block.
    """
    try:
        yield
    except LLM_SDK_ERRORS as error:
        raise _translate_llm_error(
            error, provider=provider, credential_hint=credential_hint
        ) from error
