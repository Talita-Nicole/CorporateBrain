"""Translate LLM provider SDK errors into user-facing messages."""

import logging

from openai import APIConnectionError, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

LLM_SDK_ERRORS = (AuthenticationError, RateLimitError, APIConnectionError)


class LLMServiceError(Exception):
    """LLM provider communication error carrying a user-facing message."""


def translate_llm_error(
    error: Exception, *, provider: str, credential_hint: str
) -> LLMServiceError:
    """Map an LLM provider SDK error to an ``LLMServiceError`` with a user-facing message."""
    if isinstance(error, AuthenticationError):
        message = f"Authentication failed for {provider}. Check {credential_hint}."
    elif isinstance(error, RateLimitError):
        message = (
            f"Request limit exceeded for {provider}. "
            "Wait a moment and try again."
        )
    elif isinstance(error, APIConnectionError):
        message = (
            f"Could not connect to {provider}. "
            "Check the endpoint and your network connection."
        )
    else:
        message = f"Unexpected error communicating with {provider}."
    logger.error("%s error: %s", provider, error)
    return LLMServiceError(message)
