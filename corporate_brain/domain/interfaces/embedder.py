"""Contract for producing text embeddings."""

from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings


class Embedder(ABC):
    """Provides the embeddings model used by the document repository."""

    @abstractmethod
    def as_langchain_embeddings(self) -> Embeddings:
        """Return the underlying LangChain embeddings model."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Return the embedding vector for a single ``text``."""
