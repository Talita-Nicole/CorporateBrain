"""ChromaDB-backed implementation of the document repository."""

import logging
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document as LangChainDocument
from langchain_core.vectorstores import VectorStoreRetriever

from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.embedder import Embedder

logger = logging.getLogger(__name__)

COLLECTION_NAME = "corporate_knowledge"


class ChromaDocumentRepository(DocumentRepository):
    """Stores and retrieves document chunks using a persistent Chroma store."""

    def __init__(self, embedder: Embedder, persist_directory: str) -> None:
        self._store = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=embedder.as_langchain_embeddings(),
            persist_directory=persist_directory,
        )

    def add_documents(self, chunks: list[LangChainDocument]) -> None:
        if not chunks:
            return
        self._store.add_documents(chunks)
        logger.info("Indexed %d chunks into %s", len(chunks), COLLECTION_NAME)

    def as_retriever(self, **search_kwargs: Any) -> VectorStoreRetriever:
        return self._store.as_retriever(**search_kwargs)

    def list_indexed_sources(self) -> list[str]:
        stored = self._store.get(include=["metadatas"])
        metadatas = stored.get("metadatas") or []
        sources = {
            metadata["source"]
            for metadata in metadatas
            if metadata and metadata.get("source")
        }
        return sorted(sources)
