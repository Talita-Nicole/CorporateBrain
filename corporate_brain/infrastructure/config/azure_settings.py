"""Azure OpenAI configuration loaded and validated from environment variables."""

from typing import TYPE_CHECKING, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from infrastructure.llm_errors import LLMServiceError

if TYPE_CHECKING:
    from infrastructure.azure_embedder import AzureEmbedder
    from infrastructure.azure_language_model import AzureLanguageModel

DEFAULT_API_VERSION = "2024-02-01"


class AzureSettings(BaseSettings):
    """Azure OpenAI settings read from the environment / ``.env`` file.

    ``azure_openai_deployment_name`` (the chat deployment) is optional: when the
    chat model comes from another provider (e.g. GitHub Models) only the embedding
    deployment is required from Azure. All values come exclusively from the
    environment; nothing is hardcoded.
    """

    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_embedding_deployment: str
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_api_version: str = DEFAULT_API_VERSION

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator(
        "azure_openai_endpoint",
        "azure_openai_api_key",
        "azure_openai_embedding_deployment",
    )
    @classmethod
    def _required_not_empty(cls, value: str, info) -> str:
        if not value or not value.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return value.strip()

    @field_validator("azure_openai_deployment_name")
    @classmethod
    def _blank_to_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        return value.strip()

    def get_embedding_client(self) -> "AzureEmbedder":
        """Build the embeddings adapter configured from these settings."""
        from infrastructure.azure_embedder import AzureEmbedder

        return AzureEmbedder(self)

    def get_llm_client(
        self, temperature: float = 0.0, max_tokens: Optional[int] = None
    ) -> "AzureLanguageModel":
        """Build the Azure chat LLM adapter; requires a chat deployment to be set."""
        if self.azure_openai_deployment_name is None:
            raise LLMServiceError(
                "No Azure chat deployment configured "
                "(AZURE_OPENAI_DEPLOYMENT_NAME). Configure a chat deployment "
                "or use LLM_PROVIDER=github."
            )
        from infrastructure.azure_language_model import AzureLanguageModel

        return AzureLanguageModel(self, temperature=temperature, max_tokens=max_tokens)
