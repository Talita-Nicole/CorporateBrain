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
