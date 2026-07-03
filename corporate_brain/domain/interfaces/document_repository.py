"""Contract for storing and retrieving indexed document chunks."""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.documents import Document as LangChainDocument
from langchain_core.vectorstores import VectorStoreRetriever


class DocumentRepository(ABC):
    """Persists document chunks and exposes them for semantic retrieval."""

    @abstractmethod
    def add_documents(self, chunks: list[LangChainDocument]) -> None:
        """Index the given chunks into the vector store."""

    @abstractmethod
    def as_retriever(self, **search_kwargs: Any) -> VectorStoreRetriever:
        """Return a retriever over the indexed chunks."""

    @abstractmethod
    def list_indexed_sources(self) -> list[str]:
        """Return the distinct source file names currently indexed."""

    @abstractmethod
    def sample_texts(self, limit: int, sources: list[str] | None = None) -> list[str]:
        """Return up to ``limit`` chunk texts, optionally scoped to ``sources``.

        Used to seed starter suggestions without a user query. Order is not
        guaranteed to be meaningful.
        """

    @abstractmethod
    def delete_by_source(self, source: str) -> None:
        """Remove all chunks belonging to the given source file."""

    @abstractmethod
    def similarity_search_with_score(
        self, query: str, k: int, filter: dict | None = None
    ) -> list[tuple[LangChainDocument, float]]:
        """Return up to ``k`` chunks matching ``query`` with a raw distance score.

        Lower scores mean more relevant (this is a distance, not a
        normalized similarity — Chroma's default space is L2). Used to gate
        low-relevance chunks out of the answer context (see
        ``AnswerQuestion``).
        """
