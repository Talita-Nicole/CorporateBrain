"""Compose user-facing messages for typed LLM call errors.

Kept in ``presentation/`` so infrastructure adapters only raise typed
exceptions (see ``infrastructure/llm_errors.py``) and never decide how a
message is phrased for the end user.
"""

from infrastructure.llm_errors import (
    LLMAuthError,
    LLMCallError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError,
)


def format_llm_call_error(error: LLMCallError) -> str:
    """Render a typed ``LLMCallError`` as a user-facing sentence."""
    if isinstance(error, LLMAuthError):
        return (
            f"Authentication failed for {error.provider}. Check {error.credential_hint}. "
            "If you just rotated the key in .env, restart the app to pick it up."
        )
    if isinstance(error, LLMRateLimitError):
        return f"Request limit exceeded for {error.provider}. Wait a moment and try again."
    if isinstance(error, LLMTimeoutError):
        return f"The call to {error.provider} timed out. Check your connection and try again."
    if isinstance(error, LLMConnectionError):
        return f"Could not connect to {error.provider}. Check the endpoint and your network connection."
    return f"Unexpected error communicating with {error.provider}."
