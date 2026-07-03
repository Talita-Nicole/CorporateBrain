"""Shared provider constants and dispatch factories for LLM/embedding clients.

Used by both the Streamlit app and the standalone connectivity test script so
they always exercise the same provider-selection code path.
"""

from typing import Optional

from domain.interfaces.embedder import Embedder
from domain.interfaces.language_model import LanguageModel
from infrastructure.config.azure_settings import AzureSettings
from infrastructure.config.github_models_settings import GitHubModelsSettings
from infrastructure.config.groq_settings import GroqSettings
from infrastructure.llm_errors import LLMServiceError

AZURE_PROVIDER = "azure"
GITHUB_PROVIDER = "github"
GROQ_PROVIDER = "groq"
VALID_PROVIDERS = (AZURE_PROVIDER, GITHUB_PROVIDER)
# Groq only offers chat completions, not embeddings, so it is a valid
# LLM_PROVIDER but not a valid EMBEDDING_PROVIDER.
VALID_CHAT_PROVIDERS = (AZURE_PROVIDER, GITHUB_PROVIDER, GROQ_PROVIDER)


def build_embedder(
    provider: str,
    azure_settings: Optional[AzureSettings],
    github_settings: Optional[GitHubModelsSettings],
) -> Embedder:
    """Build the embeddings client for ``provider``.

    Raises ``LLMServiceError`` for any provider value other than ``"azure"``
    or ``"github"`` (e.g. a typo in ``EMBEDDING_PROVIDER``) instead of
    silently falling back to Azure.
    """
    if provider not in VALID_PROVIDERS:
        raise LLMServiceError(
            f"Unknown EMBEDDING_PROVIDER: '{provider}'. "
            f"Expected one of: {', '.join(VALID_PROVIDERS)}."
        )
    if provider == GITHUB_PROVIDER:
        if github_settings is None:
            raise LLMServiceError("Embeddings configuration is missing.")
        return github_settings.get_embedding_client()
    if azure_settings is None:
        raise LLMServiceError("Embeddings configuration is missing.")
    return azure_settings.get_embedding_client()


def build_language_model(
    provider: str,
    azure_settings: Optional[AzureSettings],
    github_settings: Optional[GitHubModelsSettings],
    groq_settings: Optional[GroqSettings] = None,
) -> LanguageModel:
    """Build the chat client for ``provider``.

    Raises ``LLMServiceError`` for any provider value other than ``"azure"``,
    ``"github"`` or ``"groq"`` (e.g. a typo in ``LLM_PROVIDER``) instead of
    silently falling back to Azure.
    """
    if provider not in VALID_CHAT_PROVIDERS:
        raise LLMServiceError(
            f"Unknown LLM_PROVIDER: '{provider}'. "
            f"Expected one of: {', '.join(VALID_CHAT_PROVIDERS)}."
        )
    if provider == GROQ_PROVIDER:
        if groq_settings is None:
            raise LLMServiceError("Chat model configuration is missing.")
        return groq_settings.get_llm_client()
    if provider == GITHUB_PROVIDER:
        if github_settings is None:
            raise LLMServiceError("Chat model configuration is missing.")
        return github_settings.get_llm_client()
    if azure_settings is None:
        raise LLMServiceError("Chat model configuration is missing.")
    return azure_settings.get_llm_client()
