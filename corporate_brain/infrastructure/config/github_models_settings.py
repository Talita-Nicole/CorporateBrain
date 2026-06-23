"""GitHub Models configuration loaded and validated from environment variables."""

from typing import TYPE_CHECKING, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from infrastructure.github_models_embedder import GitHubModelsEmbedder
    from infrastructure.github_models_language_model import GitHubModelsLanguageModel

DEFAULT_ENDPOINT = "https://models.github.ai/inference"
DEFAULT_CHAT_MODEL = "openai/gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "openai/text-embedding-3-small"


class GitHubModelsSettings(BaseSettings):
    """GitHub Models settings for the OpenAI-compatible chat endpoint.

    Used when ``LLM_PROVIDER=github``. Authentication uses a GitHub token with the
    ``models:read`` permission; no Azure quota or deployment is required.
    """

    github_token: str
    github_models_endpoint: str = DEFAULT_ENDPOINT
    github_models_chat_model: str = DEFAULT_CHAT_MODEL
    github_models_embedding_model: str = DEFAULT_EMBEDDING_MODEL

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("github_token")
    @classmethod
    def _must_not_be_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return value.strip()

    def get_llm_client(
        self, temperature: float = 0.0, max_tokens: Optional[int] = None
    ) -> "GitHubModelsLanguageModel":
        """Build the GitHub Models chat adapter configured from these settings."""
        from infrastructure.github_models_language_model import (
            GitHubModelsLanguageModel,
        )

        return GitHubModelsLanguageModel(
            self, temperature=temperature, max_tokens=max_tokens
        )

    def get_embedding_client(self) -> "GitHubModelsEmbedder":
        """Build the GitHub Models embeddings adapter configured from these settings."""
        from infrastructure.github_models_embedder import GitHubModelsEmbedder

        return GitHubModelsEmbedder(self)
