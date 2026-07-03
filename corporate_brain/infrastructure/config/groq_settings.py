"""Groq configuration loaded and validated from environment variables."""

from typing import TYPE_CHECKING, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from infrastructure.groq_language_model import GroqLanguageModel

DEFAULT_ENDPOINT = "https://api.groq.com/openai/v1"
DEFAULT_CHAT_MODEL = "llama-3.3-70b-versatile"


class GroqSettings(BaseSettings):
    """Groq settings for the OpenAI-compatible chat endpoint.

    Used when ``LLM_PROVIDER=groq``. Groq only offers chat completions, not
    embeddings, so ``EMBEDDING_PROVIDER`` must remain ``azure`` or ``github``.
    """

    groq_api_key: str
    groq_endpoint: str = DEFAULT_ENDPOINT
    groq_chat_model: str = DEFAULT_CHAT_MODEL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("groq_api_key")
    @classmethod
    def _must_not_be_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return value.strip()

    def get_llm_client(
        self, temperature: float = 0.0, max_tokens: Optional[int] = None
    ) -> "GroqLanguageModel":
        """Build the Groq chat adapter configured from these settings."""
        from infrastructure.groq_language_model import GroqLanguageModel

        return GroqLanguageModel(self, temperature=temperature, max_tokens=max_tokens)
