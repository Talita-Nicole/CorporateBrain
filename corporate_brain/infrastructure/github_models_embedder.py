"""GitHub Models implementation of the embeddings contract (OpenAI-compatible)."""

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from domain.interfaces.embedder import Embedder
from infrastructure.config.github_models_settings import GitHubModelsSettings
from infrastructure.llm_errors import with_llm_error_translation

_CREDENTIAL_HINT = "GITHUB_TOKEN (with models:read permission)"


class GitHubModelsEmbedder(Embedder):
    """Wraps ``OpenAIEmbeddings`` pointed at the GitHub Models endpoint."""

    def __init__(self, settings: GitHubModelsSettings) -> None:
        self._embeddings = OpenAIEmbeddings(
            base_url=settings.github_models_endpoint,
            api_key=settings.github_token,
            model=settings.github_models_embedding_model,
            check_embedding_ctx_length=False,
        )

    def as_langchain_embeddings(self) -> Embeddings:
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        with with_llm_error_translation("GitHub Models", _CREDENTIAL_HINT):
            return self._embeddings.embed_query(text)
