"""Azure OpenAI implementation of the embeddings contract."""

from langchain_core.embeddings import Embeddings
from langchain_openai import AzureOpenAIEmbeddings

from domain.interfaces.embedder import Embedder
from infrastructure.config.azure_settings import AzureSettings
from infrastructure.llm_errors import LLM_SDK_ERRORS, translate_llm_error

_CREDENTIAL_HINT = "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT"

# Low-tier (S0) embedding deployments are easily rate-limited. The OpenAI client
# retries 429 responses with backoff, honoring the server's Retry-After header.
EMBEDDING_MAX_RETRIES = 6
# Texts embedded per request; smaller batches spread load under tight rate limits.
EMBEDDING_BATCH_SIZE = 16


class AzureEmbedder(Embedder):
    """Wraps ``AzureOpenAIEmbeddings`` behind the ``Embedder`` contract."""

    def __init__(self, settings: AzureSettings) -> None:
        self._embeddings = AzureOpenAIEmbeddings(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_embedding_deployment,
            api_version=settings.azure_openai_api_version,
            max_retries=EMBEDDING_MAX_RETRIES,
            chunk_size=EMBEDDING_BATCH_SIZE,
        )

    def as_langchain_embeddings(self) -> Embeddings:
        return self._embeddings

    def embed_query(self, text: str) -> list[float]:
        try:
            return self._embeddings.embed_query(text)
        except LLM_SDK_ERRORS as error:
            raise translate_llm_error(
                error, provider="Azure OpenAI", credential_hint=_CREDENTIAL_HINT
            ) from error
