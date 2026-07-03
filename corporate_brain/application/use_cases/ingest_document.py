"""Use case: process a document and index it into the knowledge base."""

import logging

from domain.interfaces.document_loader import DocumentLoader
from domain.interfaces.document_repository import DocumentRepository

logger = logging.getLogger(__name__)


class EmptyDocumentError(Exception):
    """Raised when a document yields no extractable text (e.g. a scanned PDF)."""

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        super().__init__(f"No extractable text found in '{file_name}'")


class IngestDocument:
    """Loads, chunks and indexes a single document."""

    def __init__(
        self, loader: DocumentLoader, repository: DocumentRepository
    ) -> None:
        self._loader = loader
        self._repository = repository

    def execute(self, file_path: str, file_name: str) -> int:
        """Index ``file_path`` and return the number of chunks stored.

        Raises ``EmptyDocumentError`` instead of silently indexing zero
        chunks — a scanned PDF or corrupt/empty file should not be marked
        as successfully processed.
        """
        chunks = self._loader.load_and_split(file_path, file_name)
        if not chunks:
            raise EmptyDocumentError(file_name)
        self._repository.add_documents(chunks)
        logger.info("Ingested %s into %d chunks", file_name, len(chunks))
        return len(chunks)
